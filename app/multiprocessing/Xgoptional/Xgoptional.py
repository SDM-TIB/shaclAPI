"""
Created on Jul 10, 2011

Implements the Xgoptional operator.
The intermediate results are represented as queues.

@author: Maribel Acosta Deibe
"""
import signal
from multiprocessing import Queue
from queue import Empty
from tempfile import NamedTemporaryFile
from time import time
from os import remove
from .OperatorStructures import Record, RJTTail, FileDescriptor

import logging
logger = logging.getLogger(__name__) 

class Xgoptional():

    def __init__(self, vars_left, vars_right, memory_size):
        self.left_table  = dict()
        self.right_table = dict()
        self.qresults    = Queue()
        self.bag         = [] # used to store results, which not have found a join partner, such that the result can be added in stage 3
        self.vars_left   = set(vars_left)
        self.vars_right  = set(vars_right)
        self.vars        = list(self.vars_left & self.vars_right)

        # Second stage settings
        self.secondStagesTS     = []
        self.lastSecondStageTS  = float("-inf")
        self.timeoutSecondStage = 100000000
        self.sourcesBlocked     = False

        # Main memory settings
        self.memorySize   = memory_size        # Represents the main memory size (# tuples).OLD:Represents the main memory size (in KB).
        self.fileDescriptor_left = {}
        self.fileDescriptor_right = {}
        self.memory_left  = 0
        self.memory_right = 0

        self.leftcount = 0
        self.rightcount = 0


    def instantiate(self, d):
        newvars_left = self.vars_left - set(d.keys())
        newvars_right = self.vars_right - set(d.keys())
        return Xgoptional(newvars_left, newvars_right)

    def instantiateFilter(self, instantiated_vars, filter_str):

        newvars_left = self.vars_left - set(instantiated_vars)
        newvars_right = self.vars_right - set(instantiated_vars)
        return Xgoptional(newvars_left, newvars_right)

    def execute(self, left, right, out, processqueue=Queue()):
        # Executes the Xgoptional.
        self.left     = left
        self.right    = right
        self.qresults = out

        # Initialize tuples.
        tuple1 = None
        tuple2 = None

        # Create alarm to go to stage 2.
        signal.signal(signal.SIGALRM, self.stage2)

        # Get the tuples from the queues.
        while (not(tuple1 == "EOF") or not(tuple2 == "EOF")):

            # Try to get and process tuple from left queue.
            if (not(tuple1 == "EOF")):

                try:
                    tuple1 = self.left.get(block=False)
                    if not(tuple1 == "EOF"):
                        self.bag.append(tuple1)
                    self.leftcount += 1
                    signal.alarm(self.timeoutSecondStage)
                    self.stage1(tuple1, self.left_table, self.right_table, self.vars_right)
                    self.memory_right += 1
                    #print  "bag after stage 1: ", self.bag
                except Empty:
                    # Empty: in tuple1 = self.left.get(False), when the queue is empty.
                    pass
                except TypeError as te:
                    logger.warn("TypeError: in resource = resource + tuple[var]" +  str(tuple) + str(te))
                    # TypeError: in resource = resource + tuple[var], when the tuple is "EOF".
                    pass
                except IOError:
                    # IOError: when a tuple is received, but the alarm is fired.
                    self.sourcesBlocked = False
                    pass

            # Try to get and process tuple from right queue.
            if (not(tuple2 == "EOF")):

                try:
                    tuple2 = self.right.get(block=False)
                    self.rightcount +=1
                    signal.alarm(self.timeoutSecondStage)
                    self.stage1(tuple2, self.right_table, self.left_table, self.vars_left)
                    self.memory_left += 1
                except Empty:
                    # Empty: in tuple2 = self.right.get(False), when the queue is empty.
                    pass
                except TypeError as te:
                    logger.warn("TypeError: in resource = resource + tuple[var]" +  str(tuple) + str(te))
                    # TypeError: in resource = resource + tuple[var], when the tuple is "EOF".
                    pass
                except IOError:
                    # IOError: when a tuple is received, but the alarm is fired.
                    self.sourcesBlocked = False
                    pass
            if (len(self.left_table) + len(self.right_table) >= self.memorySize):
                self.flushRJT()

        # Turn off alarm to stage 2.
        signal.alarm(0)
        #print " Perform the last probes."
        self.stage3()


    def stage1(self, tuple, tuple_rjttable, other_rjttable, vars):
        # Stage 1: While one of the sources is sending data.
        #print "stage 1"
        # Get the resource associated to the tuples.
        if tuple != "EOF":
            resource = ''
            for var in self.vars:
                val = tuple[var]
                if "^^<" in val:
                    val = val[:val.find('^^<')]
                resource = resource + str(val)
            #print "probe"
            # Probe the tuple against its RJT table.
            probeTS = self.probe(tuple, resource, tuple_rjttable, vars)
            #print "creating record"
            # Create the records.
            record = Record(tuple, probeTS, time(), float("inf"))
            #print "Stage 1"
            # Insert the record in the other RJT table.
            # TODO: use RJTTail. Check ProbeTS
            if resource in other_rjttable:
                other_rjttable.get(resource).updateRecords(record)
                other_rjttable.get(resource).setRJTProbeTS(probeTS)
                #other_rjttable.get(resource).append(record)
            else:
                tail = RJTTail(record, probeTS)
                other_rjttable[resource] = tail
                #other_rjttable[resource] = [record]

    def stage2(self, signum, frame):
        #print " Stage 2: When both sources become blocked."
        self.sourcesBlocked = True

        # Get common resources.
        resources1 = set(self.left_table.keys()) & set(self.fileDescriptor_right.keys())
        resources2 = set(self.right_table.keys()) & set(self.fileDescriptor_left.keys())

        # Iterate while there are common resources and both sources are blocked.
        while((resources1 or resources2) and self.sourcesBlocked):

            if (resources1):
                resource = resources1.pop()
                rjts1 = self.left_table[resource].records
                for rjt1 in rjts1:
                    probed = self.probeFile(rjt1, self.fileDescriptor_right, resource, 2)
                    if (probed):
                        rjt1.probeTS = time()

            elif (resources2):
                resource = resources2.pop()
                rjts1 = self.right_table[resource].records
                for rjt1 in rjts1:
                    probed = self.probeFile(rjt1, self.fileDescriptor_left, resource, 2)
                    if (probed):
                        rjt1.probeTS = time()

        # End of second stage.
        self.lastSecondStageTS = time()
        self.secondStagesTS.append(self.lastSecondStageTS)

    def stage3(self):
        # Stage 3: When both sources sent all the data.
        #print "stage 3"
        # This is the optional: Produce tuples that haven't matched already.
        #print "Length of data in xgoptional(): ", len(self.bag)

        # RJTs in main (left) memory are probed against RJTs in secondary (right) memory.
        common_resources = set(self.left_table.keys()) & set(self.fileDescriptor_right.keys())
        for resource in common_resources:
            rjts1 = self.left_table[resource].records
            for rjt1 in rjts1:
                self.probeFile(rjt1, self.fileDescriptor_right, resource, 3)

        # RJTs in main (right) memory are probed against RJTs in secondary (left) memory.
        common_resources = set(self.right_table.keys()) & set(self.fileDescriptor_left.keys())
        for resource in common_resources:
            rjts1 = self.right_table[resource].records
            for rjt1 in rjts1:
                self.probeFile(rjt1, self.fileDescriptor_left, resource, 3)

        # RJTs in secondary memory are probed to produce new results.
        common_resources = set(self.fileDescriptor_left.keys()) & set(self.fileDescriptor_right.keys())
        for resource in common_resources:
            file1 = open(self.fileDescriptor_right[resource].file.name)
            rjts1 = file1.readlines()
            for rjt1 in rjts1:
                (tuple1, probeTS1, insertTS1, flushTS1) = rjt1.split('|')
                self.probeFile(Record(eval(tuple1), float(probeTS1), float(insertTS1), float(flushTS1)), self.fileDescriptor_left, resource, 3)
            file1.close()

        for resource in common_resources:
            file1 = open(self.fileDescriptor_left[resource].file.name)
            rjts1 = file1.readlines()
            for rjt1 in rjts1:
                (tuple1, probeTS1, insertTS1, flushTS1) = rjt1.split('|')
                self.probeFile(Record(eval(tuple1), float(probeTS1), float(insertTS1), float(flushTS1)), self.fileDescriptor_right, resource, 3)
            file1.close()

        # Delete files from secondary memory.
        for resource in self.fileDescriptor_left:
            remove(self.fileDescriptor_left[resource].file.name)

        for resource in self.fileDescriptor_right:
            remove(self.fileDescriptor_right[resource].file.name)


        for tuple in self.bag:
            vars_to_add = self.vars_right.difference(set(tuple.keys()))
            for var in vars_to_add:
                tuple.update({var: None})
            self.qresults.put(tuple)

        # Put EOF in queue and exit.
        self.qresults.put("EOF")
        return

    def probe(self, tuple, resource, rjttable, vars):
        probeTS = time()
        # If the resource is in table, produce results.
        try:
            if resource in rjttable:
                rjttable.get(resource).setRJTProbeTS(probeTS)
                list_records = rjttable[resource].records
                # Delete tuple from bag.
                try:
                    self.bag.remove(tuple)
                except ValueError:
                    pass

                for record in list_records:
                    #print "record: ", type(record.tuple), record.tuple
                    if isinstance(record.tuple, dict):
                        res = record.tuple.copy()
                        res.update(tuple)
                        self.qresults.put(res)

                        # Delete tuple from bag.
                        try:
                            self.bag.remove(record.tuple)
                        except ValueError:
                            pass
        except Exception as e:
            pass
        return probeTS

    def probeFile(self, rjt1, filedescriptor2, resource, stage):
        # Probe an RJT against its corresponding partition in secondary memory.

        file2 = open(filedescriptor2[resource].file.name, 'r')
        rjts2 = file2.readlines()
        st = ""
        probed = False

        for rjt2 in rjts2:
            (tuple2, probeTS2, insertTS2, flushTS2) = rjt2.split('|')
            probedStage1 = False
            probedStage2 = False

            #Checking Property 2: Probed in stage 2.
            for ss in self.secondStagesTS:
                if (float(flushTS2) < rjt1.insertTS and rjt1.insertTS < ss and  ss < rjt1.flushTS):
                    probedStage2 = True
                    break

            # Checking Property 1: Probed in stage 1.
            if (rjt1.probeTS < float(flushTS2)):
                probedStage1 = True

            # Produce result if it has not been produced.
            if (not(probedStage1) and not(probedStage2)):
                res = rjt1.tuple.copy()
                tuple2_evaluated = eval(tuple2)
                res.update(tuple2_evaluated)
                self.qresults.put(res)

                # Delete tuple from bag.
                try:
                    self.bag.remove(rjt1.tuple)
                except ValueError:
                    pass

                try:
                    self.bag.remove(tuple2_evaluated)
                except ValueError:
                    pass

                probed = True

            # Update probeTS of tuple2.
            stprobeTS  = "%.40r" % (time())
            st = st + tuple2 + '|' + stprobeTS + '|' + insertTS2 + '|' + flushTS2

        file2.close()

        # Update file2 if in stage 2.
        if ((stage == 2) and probed):
            file2 = open(filedescriptor2[resource].file.name, 'w')
            file2.write(st)
            file2.close()

        return probed

    def flushRJT(self):
        # Flush an RJT to secondary memory.

        # Choose a victim from each partition (table).
        (resource_to_flush1, tail_to_flush1, least_ts1) = self.getVictim(self.left_table)
        (resource_to_flush2, tail_to_flush2, least_ts2) = self.getVictim(self.right_table)

        # Flush resource from left table.
        if least_ts1 <= least_ts2:
            file_descriptor = self.fileDescriptor_left
            table = self.left_table
            resource_to_flush = resource_to_flush1
            tail_to_flush = tail_to_flush1

        # Flush resource from right table.
        if least_ts2 < least_ts1:
            file_descriptor = self.fileDescriptor_right
            table = self.right_table
            resource_to_flush = resource_to_flush2
            tail_to_flush = tail_to_flush2

        # Create flush timestamp.
        flushTS = time()

        # Update file descriptor
        if (resource_to_flush in file_descriptor):
            lentail = file_descriptor[resource_to_flush].size
            file = open(file_descriptor[resource_to_flush].file.name, 'a')
            file_descriptor.update({resource_to_flush: FileDescriptor(file, len(tail_to_flush.records) + lentail, flushTS)})
        else:
            file = NamedTemporaryFile(mode="w+", suffix=".rjt", prefix="", delete=False)
            file_descriptor.update({resource_to_flush: FileDescriptor(file, len(tail_to_flush.records), flushTS)})

        # Flush tail in file.
        for record in tail_to_flush.records:
            sttuple    = str(record.tuple)
            stprobeTS  = "%.40r" % (record.probeTS)
            stinsertTS = "%.40r" % (record.insertTS)
            stflushTS  = "%.40r" % (flushTS)

            file.write(sttuple + '|')
            file.write(stprobeTS + '|')
            file.write(stinsertTS + '|')
            file.write(stflushTS + '\n')
        file.close()

        # Delete resource from main memory.
        del table[resource_to_flush]

    def getVictim(self, table):
        # Selects a victim from a partition in main memory to flush.

        resource_to_flush = ""
        tail_to_flush = RJTTail([], 0)
        least_ts = float("inf")

        for resource, tail in table.items():
            resource_ts = tail.rjtProbeTS
            if ((resource_ts < least_ts) or
                (resource_ts == least_ts and len(tail.records) > len(tail_to_flush.records))):
                resource_to_flush = resource
                tail_to_flush = tail
                least_ts = resource_ts

        #print "Victim chosen:", resource_to_flush, "TS:", least_ts, "LEN:", len(tail_to_flush.records)
        return (resource_to_flush, tail_to_flush, least_ts)

    def getLargestRJTs(self, i):
        # Selects the i-th largest RJT stored in secondary memory.

        sizes1 = set(map(FileDescriptor.getSize, self.fileDescriptor_left.values()))
        sizes2 = set(map(FileDescriptor.getSize, self.fileDescriptor_right.values()))

        sizes1 = list(sizes1)
        sizes2 = list(sizes2)

        sizes1.sort()
        sizes2.sort()

        if (sizes1 and sizes2):
            if (sizes1[len(sizes1)-1] > sizes2[len(sizes2)-1]):
                file_descriptor = self.fileDescriptor_left
                max_len = sizes1[len(sizes1)-(i+1)]
                table = self.right_table
            else:
                file_descriptor = self.fileDescriptor_right
                max_len = sizes2[len(sizes2)-(i+1)]
                table = self.left_table
        elif (sizes1):
            file_descriptor = self.fileDescriptor_left
            max_len = sizes1[len(sizes1)-(i+1)]
            table = self.right_table
        else:
            file_descriptor =self.fileDescriptor_right
            max_len = sizes2[len(sizes2)-(i+1)]
            table = self.left_table

        largestRJTs = {}

        for resource, fd in file_descriptor.items():
            if (fd.size == max_len):
                largestRJTs[resource] = fd

        return (largestRJTs, table)