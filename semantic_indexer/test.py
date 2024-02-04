#!/usr/bin/python
# -*- coding: utf-8 -*

# !!!!!!!!!  FIRST CONFIGURE SETTINGS.YAML TO MATCH YOUR NEEDS !!!!!!!!!!
# Simple script to run the Pipeline Wrapper,


import logging
import pika
import json
from medknow.tasks import taskCoordinator
from medknow.config import settings
from medknow.utilities import time_log, log_capture_string
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

global JOBID





# ### Create the logger
# logger = logging.getLogger('basic_logger')
# logger.setLevel(logging.DEBUG)




### Setup the console handler with a StringIO object
# log_capture_string = io.StringIO()
# logging.getLogger("pika").setLevel(logging.WARNING)


# logging.basicConfig(
#     level=logging.DEBUG,
#     format="%(asctime)s - %(message)s",
#     handlers=[
#         logging.StreamHandler(log_capture_string)
#         #log_stream
#     ])



def LISTEN_TO_RABBIT():

    con_credentials = pika.PlainCredentials(settings['rabbit_mq']['user'], settings['rabbit_mq']['password'])
    con_parameters = pika.ConnectionParameters(host=settings['rabbit_mq']['host'], port=int(settings['rabbit_mq']['port']),
                                               credentials=con_credentials)
    connection = pika.BlockingConnection(con_parameters)
    channel = connection.channel()
    read_queue = 'iasis.' + settings['rabbit_mq']['mod_name'] + '.queue'
    channel.queue_declare(queue=read_queue, durable=True)
    channel.exchange_declare('iasis.direct', exchange_type='direct',  durable=True)
    channel.queue_bind(exchange='iasis.direct',
    queue=read_queue,
    routing_key='iasis.' + settings['rabbit_mq']['mod_name'] + '.routingkey')

    def callback(ch, method, properties, bd):
        global JOBID
        bd2 = json.loads(bd)
        JOBID = bd2['jobID']
        time_log(" [x] Received %r" % bd)
        ch.stop_consuming()

    channel.basic_consume(callback,
                          queue=read_queue,
                          no_ack=True)

    time_log(' [*] Waiting for messages. Consuming one message from %s' % read_queue)
    channel.start_consuming()
    connection.close()
    time_log("RECEIVED JOBID %s" % JOBID)
    return 1

def WRITE_TO_RABBIT(resp, msg):
    con_credentials = pika.PlainCredentials(settings['rabbit_mq']['user'], settings['rabbit_mq']['password'])
    con_parameters = pika.ConnectionParameters(host=settings['rabbit_mq']['host'], port=int(settings['rabbit_mq']['port']),
                                               credentials=con_credentials)
    connection = pika.BlockingConnection(con_parameters)
    channel = connection.channel()
    channel.queue_declare(queue='iasis.orchestrator.queue', durable=True)
    channel.exchange_declare('iasis.direct', exchange_type='direct',  durable=True)
    channel.queue_bind(queue="iasis.orchestrator.queue",
                        exchange='iasis.direct',
                        routing_key="iasis.orchestrator.routingkey")
    if type(msg) == list:
        msg = " ".join(msg)
    body = json.dumps({"jobID":JOBID, "componentName":settings['rabbit_mq']['mod_name'], "MESSAGE":resp, "LOGS":msg})
    channel.basic_publish('iasis.direct'
                          ,'iasis.orchestrator.routingkey', body=body, properties=pika.BasicProperties(delivery_mode = 2))
    time_log("Sent '%s'"% body)
    connection.close()




def main():
    # ### Create the logger
    # logger = logging.getLogger('basic_logger')
    # logger.setLevel(logging.NOTSET)

    # ### Setup the console handler with a StringIO object
    # log_capture_string = io.StringIO()
    # ch = logging.StreamHandler(log_capture_string)
    # ch.setLevel(logging.NOTSET)

    # ### Optionally add a formatter
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # ch.setFormatter(formatter)

    # ### Add the console handler to the logger
    # logger.addHandler(ch)

    try:
        #LISTEN_TO_RABBIT() # without rabbit

        TaskManager = taskCoordinator()
        TaskManager.print_pipeline()
        TaskManager.run()
        resp = "STATUS OK!"
    except Exception, e:
        resp = "PROBLEM! %s" % e
    #from medknow.utilities import all_str
    #WRITE_TO_RABBIT(resp, str(all_str))
    exit(1)

if __name__ == '__main__':
    main()
