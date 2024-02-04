#!/usr/bin/python !/usr/bin/env python
# -*- coding: utf-8 -*


# Functions tha combine modular subfunctions creating
# a task to complete, such as reading from file, extracting concepts
# and saving to disk again.

from time import sleep
from config import settings
from utilities import time_log
from subprocess import call, Popen, PIPE
from medknow.data_extractor import runProcess
from data_loader import load_mongo, load_mongo_batches, \
                        parse_remove_edges, parse_text, get_collection_count
from data_extractor import extract_semrep, extract_semrep_parallel, \
                           get_concepts_from_edges, get_concepts_from_edges_parallel                          
from data_saver import save_neo4j, create_neo4j_results, create_neo4j_csv, \
                     update_neo4j, update_mongo_sentences, save_mongo, update_neo4j_parallel
from tqdm import tqdm




class Parser(object):
    """
    Parser class for reading input. According to which pipeline
    task it is called upon, it parses the appropriate file.
    Filepaths and details according to settings.yaml.
    """

    def __init__(self, source, key, name=None):
        """
        Initialization of the class.
        Attributes:
            - source: str, value denoting where we will read from (e.g 'mongo')
            - type: str, value denoting what we will read (e.g. text, edges)
            - name: str, The name is only for pretty-printing purposes.
        """

        self.source = source
        self.key = key
        parallel_flag = str(settings['pipeline']['in']['parallel']) == 'True'
        stream_flag = str(settings['pipeline']['in']['stream']) == 'True'
        if self.source == 'mongo':
            if parallel_flag or stream_flag:
                self.load = load_mongo_batches
            else:
                self.load = load_mongo
        elif self.source == 'delete':
            self.load = parse_remove_edges
        else:
            time_log('Source to read was %s. Please change settings' % self.source)
            raise NotImplementedError
        if self.key == 'text':
            self.parse = parse_text 
        elif self.key == 'med_red':
            self.parse = None
        elif self.key == 'edges':
            self.parse = None
        else:
            time_log('Type to read was %s. Please change settings' % self.key)
            raise NotImplementedError
        if name:
            self.name = name
        else:
            self.name = 'Type: %s From : %s' % (self.source, self.key)

    def read(self, N=None, ind_=0):
        """
        Run the corresponding parsing function and return:
        Input:
            - ind_: int, the starting point to read from
        Output: 
        1) In case of the batch or streaming processing:
            - json_: dict, the corresponding read batch
            - N: int, the total number of items to iterate through
            - ind_: int, the index where the next iteration of readings
            should start from
            
        2) In case of loading the whole collection:
            - json_: dict, the corresponding collection
        """
        parallel_flag = str(settings['pipeline']['in']['parallel']) == 'True'
        stream_flag = str(settings['pipeline']['in']['stream']) == 'True'
        if parallel_flag or stream_flag:
            json_, ind_ = self.load(self.key, N, ind_)
            if json_:
                if self.parse:
                    json_ = self.parse(json_)
                time_log('Completed Parsing. Read: %d documents!' % len(json_[settings['out']['json']['itemfield']]))
            return json_, ind_
        else:
            json_ = self.load(self.key)
            if self.parse:
                json_ = self.parse(json_)
            time_log('Completed Parsing. Read: %d documents!' % len(json_[settings['out']['json']['itemfield']]))
            return json_


class Extractor(object):
    """
    Class for extracting concepts/entities and relations from medical text.
    Expects to work with json files generated from the corresponding Parser
    objects. Currently ['semrep'] implemented.
    Filepaths and details according to settings.yaml.
    """

    def __init__(self, key, parser_key, name=None):
        """
        Initialization of the class.
        Input:
            - key: str,
            string denoting what extraction task is to take place
            - parser_key: str,
            string denoting what type of input to expect
            - name: str,
            optional string for the tast to be printed
        """

        self.key = key
        self.parser_key = parser_key
        if self.key == 'semrep':
            if str(settings['pipeline']['in']['parallel']) == 'True':
                self.func = extract_semrep_parallel
                time_log('Will use multiprocessing for the semrep extraction!')
            else:
                self.func = extract_semrep
        elif self.key == 'metamap':
            self.func = extract_metamap
            # self.func = extract_metamap
        elif self.key == 'reverb':
            raise NotImplementedError
        elif self.key == 'get_concepts_from_edges':
            if str(settings['pipeline']['in']['parallel']) == 'True':
                self.func = get_concepts_from_edges_parallel
            else:
                self.func = get_concepts_from_edges
            # self.func = extract_reverb
        if name:
            self.name = name
        else:
            self.name = self.key

    def run(self, json):
        """
        Run the corresponding extracting function and return the .json_
        dictionary result.
        """

        if type(json) == dict:
            json_ = self.func(json, self.parser_key)
            time_log('Completed extracting using %s!' % self.name)
        else:
            time_log('Unsupported type of json to work on!')
            time_log('Task : %s  --- Type of json: %s' % (self.name, type(json)))
            time_log(json)
            json_ = {}
        return json_


class Dumper(object):
    """
    Class for saving the extracted results. Expects to work with json files
    generated from the previous extraction phases. Currently implemented
    dumping methods for keys:
        -json : for the enriched medical documents
        -csv : for nodes, relations before importing into neo4j
        -neo4j: for nodes, relations updating neo4j db directly
    Filepaths and details according to settings.yaml.
    Params:
        - key: str,
        one of the json, csv, neo4j
        - inp_key: str,
        the Parser key for this pipeline
        - name: str,
        Name of the Dumper. For printing purposes only
    """

    def __init__(self, key, inp_key='text', name=None):
        self.key = key

        if self.key == 'neo4j':
            self.transform = create_neo4j_results
            parallel_flag = str(settings['pipeline']['in']['parallel']) == 'True'
            self.func = update_neo4j
            if parallel_flag:
                self.func = update_neo4j_parallel
        elif self.key == 'mongo_sentences':
            self.transform = None
            self.func = update_mongo
        elif self.key == 'mongo':
            self.transform = None
            self.func = save_mongo
        if inp_key == 'text':
            self.type_ = 'harvester'
        elif inp_key == 'edges':
            self.type_ = 'edges'
        if name:
            self.name = name
        else:
            self.name = self.key

    def save(self, json_):
        if type(json_) == dict:
            if self.transform:
                results = self.transform(json_, self.type_)
            else:
                results = json_ 
            json_ = self.func(results)
            time_log('Completed saving data. Results saved in:\n %s' % settings['out'][self.key]['out_path'])
        else:
            time_log('Unsupported type of json to work on!')
            time_log('Task : %s  --- Type of json: %s' % (self.name, type(json)))
            time_log(json)
            json_ = {}
        return json_


class taskCoordinator(object):
    """
    Orchestrator class for the different saving values.
    """

    def __init__(self):
        self.pipeline = {}
        self.phases = ['in', 'trans', 'out']
        for phase, dic_ in sorted(settings['pipeline'].iteritems()):
            self.pipeline[phase] = {}
            for key, value in dic_.iteritems():
                if value:
                    self.pipeline[phase][key] = value

    def run2(self):
        print settings['load']['path']['semrep']
        import os, pymongo
        print(os.path.isdir(settings['load']['path']['semrep']))
        print "SEMREP SEEMS OK"
        print settings['load']['path']['metamap']
        import os
        print(os.path.isdir(settings['load']['path']['metamap']))
        print "METAMAP SEEMS OK"
        uri = settings['load']['mongo']['uri']
        db_name = settings['load']['mongo']['db']
        collection_name = settings['load']['mongo']['collection']
        client = pymongo.MongoClient(uri)
        db = client[db_name]
        collection = db[collection_name]
        N_collection = collection.count()
        print "MONGO"
        print settings['load']['mongo']['collection']
        print N_collection

    def run(self):
        parallel_flag = False
        stream_flag = False    
        if 'parallel' in self.pipeline['in']:
            parallel_flag = True
        if 'stream' in self.pipeline['in']:
            stream_flag = True
        if parallel_flag or stream_flag:
            parser = Parser(self.pipeline['in']['source'], self.pipeline['in']['type'])
            ind_ = 0
            N = get_collection_count(parser.source, parser.key)
            while ind_ < N:
                old_ind = ind_
                json_all, ind_ = parser.read(N=N, ind_=ind_)
                #break
                #print 'fetched'
                #print json_all, ind_
                outfield = settings['out']['json']['itemfield']
                if json_all:
                    json_ = json_all
                    for phase in self.phases:
                        dic = self.pipeline[phase]
                        if phase == 'trans':
                            for key, value in dic.iteritems():
                                if value:
                                    extractor = Extractor(key, parser.key)
                                    json_ = extractor.run(json_)
                        if phase == 'out':
                            for key, value in sorted(dic.iteritems()):
                                if value:
                                    dumper = Dumper(key, parser.key)
                                    dumper.save(json_)
                if ind_:
                    time_log('Processed %d documents in parallel. We are at index %d!' % (ind_ - old_ind, ind_))
                    proc = int(ind_/float(N)*100)
                if proc % 10 == 0 and proc > 0:
                    time_log('~'*50)
                    time_log('We are at %d/%d documents processed -- %0.2f %%' % (ind_, N, proc))
                    time_log('~'*50)
        else:
            parser = Parser(self.pipeline['in']['source'], self.pipeline['in']['type'])
            json_ = parser.read()
            for phase in self.phases:
                dic = self.pipeline[phase]
                if phase == 'trans':
                    for key, value in dic.iteritems():
                        if value:
                            extractor = Extractor(key, parser.key)
                            json_ = extractor.run(json_)
                if phase == 'out':
                    for key, value in sorted(dic.iteritems()):
                        if value:
                            dumper = Dumper(key, parser.key)
                            dumper.save(json_)

        # else:
        #     if 'stream' in self.pipeline['in']:
        #         stream_flag = True
        #     else:
        #         stream_flag = False
        #     if stream_flag:
        #         if self.pipeline['in']['inp'] == 'json' or self.pipeline['in']['inp'] == 'edges':
        #             inp_path = settings['load'][self.pipeline['in']['inp']]['inp_path']
        #             if self.pipeline['in']['inp'] == 'json':
        #                 outfield_inp = settings['load'][self.pipeline['in']['inp']]['docfield']
        #             elif self.pipeline['in']['inp'] == 'edges':
        #                 outfield_inp = settings['load'][self.pipeline['in']['inp']]['edge_field']
        #             else:
        #                 raise NotImplementedError
        #             outfield_out = settings['out']['json']['itemfield']
        #             c = 0
        #             with open(inp_path, 'r') as f:
        #                 docs = ijson2.items(f, '%s.item' % outfield_inp)
        #                 for item in docs:
        #                     c += 1
        #                     if c < 0:
        #                         continue
        #                     print c
        #                     time_log(c)
        #                     json_ = {outfield_out:[item]}
        #                     if self.pipeline['in']['inp'] == 'json':
        #                         json_ = parse_json(json_)
        #                     elif self.pipeline['in']['inp'] == 'edges':
        #                         json_ = parse_edges(json_)
        #                     parser = Parser(self.pipeline['in']['inp'])
        #                     for phase in self.phases:
        #                         dic = self.pipeline[phase]
        #                         if phase == 'trans':
        #                             for key, value in dic.iteritems():
        #                                 if value:
        #                                     extractor = Extractor(key, parser.key)
        #                                     json_ = extractor.run(json_)
        #                         if phase == 'out':
        #                             for key, value in sorted(dic.iteritems()):
        #                                 if value:
        #                                     dumper = Dumper(key, self.pipeline['in']['inp'])
        #                                     dumper.save(json_)

        #                 if int(c) % 1000 == 0 and c > 1000:
        #                     time_log('Processed %d documents in stream mode!' % (c))
        #         elif self.pipeline['in']['inp'] == 'mongo':
        #             parser = Parser(self.pipeline['in']['inp'])
        #             ind_ = 0#2390
        #             while ind_ or (ind_ == 0):
        #                 old_ind = ind_
        #                 json_all, ind_, N = parser.read(ind_)
        #                 if not(ind_):
        #                     break
        #                 outfield = settings['out']['json']['itemfield']
        #                 if json_all:
        #                     json_ = json_all
        #                     for phase in self.phases:
        #                         dic = self.pipeline[phase]
        #                         if phase == 'trans':
        #                             for key, value in dic.iteritems():
        #                                 if value:
        #                                     extractor = Extractor(key, parser.key)
        #                                     json_ = extractor.run(json_)
        #                         if phase == 'out':
        #                             for key, value in sorted(dic.iteritems()):
        #                                 if value:
        #                                     dumper = Dumper(key, parser.key)
        #                                     dumper.save(json_)
        #                 if ind_:
        #                     time_log('Processed %d documents in parallel. We are at index %d!' % (ind_ - old_ind, ind_))
        #                     proc = int(ind_/float(N)*100)
        #                 if proc % 10 == 0 and proc > 0:
        #                     time_log('~'*50)
        #                     time_log('We are at %d/%d documents processed -- %0.2f %%' % (ind_, N, proc))
        #                     time_log('~'*50)

            # parser = Parser(self.pipeline['in']['inp'])
            # outfield = settings['out']['json']['itemfield']
            # json_all = parser.read()
            # if stream_flag:
            #     for item in json_all[outfield]:
            #         json_ = {outfield:[item]}
            #         for phase in self.phases:
            #             dic = self.pipeline[phase]
            #             if phase == 'trans':
            #                 for key, value in dic.iteritems():
            #                     if value:
            #                         extractor = Extractor(key, parser.key)
            #                         json_ = extractor.run(json_)
            #             if phase == 'out':
            #                 for key, value in sorted(dic.iteritems()):
            #                     if value:
            #                         dumper = Dumper(key, parser.key)
            #                         dumper.save(json_)

            


        # parser = Parser(self.pipeline['in']['inp'])
        # out_outfield = settings['out']['json']['itemfield']
        # json_ = parser.read()
        # for doc in tqdm(json_[out_outfield]):
        #     tmp = {out_outfield:[doc]}
        #     for phase in self.phases:
        #         dic = self.pipeline[phase]
        #         if phase == 'in':
        #             pass
        #         if phase == 'trans':
        #             for key, value in dic.iteritems():
        #                 if value:
        #                     extractor = Extractor(key, parser.key)
        #                     tmp = extractor.run(tmp)
        #         if phase == 'out':
        #             for key, value in sorted(dic.iteritems()):
        #                 if value:
        #                     dumper = Dumper(key, parser.key)
        #                     dumper.save(tmp)

    def print_pipeline(self):
        print('#'*30 + ' Pipeline Schedule' + '#'*30)
        for phase in self.phases:
            dic = self.pipeline[phase]
            if phase == 'in':
                if dic['source'] == 'delete':
                    print("Will delete all %s resource associated edges!" % settings['neo4j']['resource'])
                    break
                if dic['source'] == 'file':
                    source = settings['load']['path']['file_path']
                elif dic['source'] == 'mongo':
                    source = settings['load']['mongo']['file_path']
                print('Will read from: %s' % source)
            if phase == 'trans':
                print('Will use the following transformation utilities:')
                for key, value in dic.iteritems():
                    print ('- %s' % key)
            if phase == 'out':
                print('Will save the outcome as follows:')
                for key, value in dic.iteritems():
                    print('%s  : %s' % (key, settings['out'][key]['out_path']))
        print('#'*30 + ' Pipeline Schedule ' + '#'*30)


    def start_metamap(self):
        print('~'*10 + " Will Start Service skrtl from Metamap "+'~'*10 )
        rc = runProcess('sh skrmedpostctl start', settings['load']['path']['metamap'])
        for results in rc:
            print(results)
        print('~'*10 + " Will Start Service wsd from Metamap "+'~'*10 )
        output = Popen(['./wsdserverctl start'], shell=True, cwd=settings['load']['path']['metamap'])
        secs = 45
        print("Initializing Word-Sense Disambiguations Server. Please wait %d secs..." % secs)
        sleep(secs)
        print('~'*15 + " Finished setting up Metamap "+'~'*15)
        return 1

    def stop_metamap(self):
        print('~'*10 + " Stopping Service skrtl from Metamap "+'~'*10 )
        rc = runProcess('sh skrmedpostctl stop', settings['load']['path']['metamap'])
        for results in rc:
            print(results)
        print('~'*10 + " Stopping Service wsd from Metamap "+'~'*10 )
        rc = runProcess('sh wsdserverctl stop', settings['load']['path']['metamap'])
        for results in rc:
            print(results)
        return 1


