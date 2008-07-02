
from franz.openrdf.repository.repository import Repository
from franz.openrdf.sail.sail import SailRepository
from franz.openrdf.sail.allegrographstore import AllegroGraphStore
from franz.openrdf.query.query import QueryLanguage
from franz.openrdf.vocabulary.rdf import RDF
from franz.openrdf.rio.rdfformat import RDFFormat
from franz.openrdf.rio.rdfwriter import RDFXMLWriter, NTriplesWriter

import os, urllib, datetime

CURRENT_DIRECTORY = os.getcwd() 

def test0():
    """
    Test to see if you have the module settings correctly set.
    """
    print "Welcome to the PythonAPI"
    file1 = open("./vc-db-1.rdf")
    print file1.name, os.path.abspath(file1.name)
    file2 = open(CURRENT_DIRECTORY + "/vc-db-1.rdf")
    print file2.name 
    
    try:
        fname, headers = urllib.urlretrieve("http://www.co-ode.org/ontologies/amino-acid/2005/10/11/amino-acid.owl", "/tmp/myfile")
        file3 = open(fname) 
    except Exception, e:
        print "Failed ", e
    for line in file3:
        print line
    print "MADE IT"
    

def test1():
    sesameDir = "/Users/bmacgregor/Desktop/SesameFolder"
    store = AllegroGraphStore(AllegroGraphStore.RENEW, "192.168.1.102", "testP",
                              sesameDir, port=4567)
    myRepository = SailRepository(store)
    myRepository.initialize()
    ## TEMPORARY:
    #store.internal_ag_store.serverTrace(True)
    ## END TEMPORARY
    print "Repository is up!"
    return myRepository
    
def test2():
    myRepository = test1()
    f = myRepository.getValueFactory()
    ## create some resources and literals to make statements out of
    alice = f.createURI("http://example.org/people/alice")
    bob = f.createURI("http://example.org/people/bob")
    name = f.createURI("http://example.org/ontology/name")
    person = f.createURI("http://example.org/ontology/Person")
    bobsName = f.createLiteral("Bob")
    alicesName = f.createLiteral("Alice")

    conn = myRepository.getConnection()
    ## alice is a person
    conn.add(alice, RDF.TYPE, person)
    ## alice's name is "Alice"
    conn.add(alice, name, alicesName)
    ## bob is a person
    conn.add(bob, RDF.TYPE, person)
    ## bob's name is "Bob":
    conn.add(bob, name, bobsName)
    return myRepository

def test3():    
    conn = test2().getConnection()
    try:
        queryString = "SELECT ?s ?p ?o WHERE {?s ?p ?o .}"
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
        result = tupleQuery.evaluate();
        try:
            for bindingSet in result:
                s = bindingSet.getValue("s")
                p = bindingSet.getValue("p")
                o = bindingSet.getValue("o")              
                print "%s %s %s" % (s, p, o)
        finally:
            result.close();
    finally:
        conn.close();
        
def test4():
    myRepository = test2()
    conn = myRepository.getConnection()
    alice = myRepository.getValueFactory().createURI("http://example.org/people/alice")
    statements = conn.getStatements(alice, None, None, True, [])
    for s in statements:
        print s
    print "Same thing using JDBC:"
    resultSet = conn.getJDBCStatements(alice, None, None, True, [])
    while resultSet.next():
        #print resultSet.getRow()
        print "   ", resultSet.getValue(3), "   ", resultSet.getString(3)  
               
import dircache, os

def test5():
    print "ABSPATH ", os.path.abspath(".")
    for f in dircache.listdir("."):
        print f
        
    myRepository = test1()       
    print "CURDIR ", os.getcwd() 
    file = open("/Users/bmacgregor/Documents/eclipse-franz-python/agraph-python/src/sesame_test/vc-db-1.rdf")        
    file = open("./vc-db-1.rdf")            
    #file = open("./agraph-python/src/sesame_test/vc-db-1.rdf")                
    baseURI = "http://example.org/example/local"
    baseURI = None
    try:
        conn = myRepository.getConnection();
        conn.add("./vc-db-1.rdf", base=baseURI, format=RDFFormat.RDFXML); 
        print "After loading, repository contains %s triples." % conn.size(None)
        try:
            for s in conn.getStatements(None, None, None, True, []):
                print s
             
#            print "\n\nAnd here it is JDBC-style"
#            resultSet = conn.getJDBCStatements(None, None, None, False, [])
#            while resultSet.next():
#                print resultSet.getRow()
                
            print "\n\nAnd here it is without the objects"
            resultSet = conn.getJDBCStatements(None, None, None, True, [])
            while resultSet.next():
                print resultSet.getString(1), resultSet.getString(2), resultSet.getString(3)

        finally:
            pass
    finally:
        conn.close()

def test6():
    myRepository = test1() 
    file = open("/Users/bmacgregor/Documents/eclipse-franz-python/agraph-python/src/sesame_test/vc-db-1.rdf")        
    baseURI = "http://example.org/example/local"
    try:
        conn = myRepository.getConnection();
        conn.add(file, base=baseURI, format=RDFFormat.RDFXML);
        print "After loading, repository contains %s triples." % conn.size(None)         
        queryString = "SELECT ?s ?p ?o WHERE {?s ?p ?o .}"
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
        result = tupleQuery.evaluate();
        try:
            for bindingSet in result:
                s = bindingSet.getValue("s")
                p = bindingSet.getValue("p")
                o = bindingSet.getValue("o")              
                print "%s %s %s" % (s, p, o)
        finally:
            result.close();
    finally:
        conn.close();
        
def test7():
    myRepository = test1() 
    file = open("/Users/bmacgregor/Documents/eclipse-franz-python/agraph-python/src/sesame_test/vc-db-1.rdf")        
    baseURI = "http://example.org/example/local"
    try:
        conn = myRepository.getConnection();
        conn.add(file, base=baseURI, format=RDFFormat.RDFXML);
        print "After loading, repository contains %s triples." % conn.size(None)         
        queryString = "CONSTRUCT { ?s ?p ?o } WHERE {?s ?p ?o .}"
        graphQuery = conn.prepareGraphQuery(QueryLanguage.SPARQL, queryString)
        result = graphQuery.evaluate();
        for s in result:          
            print s
    finally:
        conn.close();

import urlparse

def test8():
    location = "/Users/bmacgregor/Documents/eclipse-franz-python/agraph-python/src/test/vc_db_1_rdf"      
    url = "/Users/bmacgregor/Documents/eclipse-franz-python/agraph-python/src/sesame_test/vc-db-1.rdf"      
    url = "/Users/bmacgregor/Documents/eclipse-franz-python/agraph-python/src/sesame_test/sample-bad.rdf"
    baseURI = location
    myRepository = test1() 
    context = myRepository.getValueFactory().createURI(location)
    ## TEMPORARY:  
    print "NULLIFYING CONTEXT TEMPORARILY"
    context = None
    ## END TEMPORARY  
    conn = myRepository.getConnection();
    ## read the contents of a file into the context:
    conn.add(url, baseURI, format=RDFFormat.RDFXML, contexts=context);
    print "RDF store contains %s triples" % conn.size(None)
    ## Get all statements in the context
    statements = conn.getStatements(None, None, None, False, context)    
    try:
        for s in statements:
            print s
    finally:
        statements.close()
    ## Export all statements in the context to System.out, in NTriples format
    outputFile = "/users/bmacgregor/Desktop/temp.nt"
    outputFile = None
    if outputFile == None:
        print "Writing to Standard Out instead of to a file"
    ntriplesWriter = NTriplesWriter(outputFile)
    conn.export(ntriplesWriter, context);    
    ## Remove all statements in the context from the repository
    conn.clear(context)
    ## Verify that the statements have been removed:
    statements = conn.getStatements(None, None, None, False, context)    
    try:
        for s in statements:
            print s
    finally:
        statements.close()
   
def test9():
    test2()
    sesameDir = "/Users/bmacgregor/Desktop/SesameFolder"
    store = AllegroGraphStore(AllegroGraphStore.OPEN, "localhost", "testP",
                              sesameDir, port=4567)
    myRepository = SailRepository(store)
    myRepository.initialize()
    ## TEMPORARY:
    #store.internal_ag_store.serverTrace(True)
    ## END TEMPORARY
    print "Repository is up!"
    conn = myRepository.getConnection()
    statements = conn.getStatements(None, None, None, False, None)    
    try:
        for s in statements:
            print s
    finally:
        statements.close()
    return myRepository

def test10():
    myRepository = test1()
    conn = myRepository.getConnection()
    aminoFile = "amino.owl"
    aminoFile = "/Users/bmacgregor/Desktop/rdf/ciafactbook.nt"
    print "Begin loading triples from ", aminoFile, " into AG ..."
    conn.add(aminoFile)
    print "Loaded ", conn.size(None), " triples."
#    f = myRepository.getValueFactory()
#    rdfsLabel = f.createURI("http://www.w3.org/2000/01/rdf-schema#label")
#    glutamine = f.createLiteral("Glutamine")
    ##
    count = 0         
    ##statements = conn.getStatements(None, None, glutamine, True, None)
    print "Begin retrieval ", datetime.datetime.now()
    beginTime = datetime.datetime.now()    
    statements = conn.getStatements(None, None, None, False, None)
    elapsed = datetime.datetime.now() - beginTime
    print "Retrieval took %s milliseconds" % (elapsed.microseconds / 1000)
    print "Begin counting statements ... ", datetime.datetime.now()
    beginTime = datetime.datetime.now()   
    for s in statements:
        #print s
        count += 1
        if (count % 50) == 0:  print '.',
        if (count % 4000) == 0: print "M"
    elapsed = datetime.datetime.now() - beginTime
    print "Counted %i statements in %s milliseconds" % (count, (elapsed.microseconds / 1000))
    print "End retrieval ", datetime.datetime.now(), " elapsed ", elapsed
    
    print "Begin JDBC retrieval ", datetime.datetime.now()
    beginTime = datetime.datetime.now()    
    resultSet = conn.getJDBCStatements(None, None, None, False, [])
    count = 0
    while resultSet.next():
        #print s
        count += 1
        if (count % 50) == 0:  print '.',
        if (count % 1000) == 0: print
    elapsed = datetime.datetime.now() - beginTime
    print "Counted %i JDBC statements in %s milliseconds" % (count, (elapsed.microseconds / 1000))
    print "End retrieval ", datetime.datetime.now(), " elapsed ", elapsed



def test11():
    """
    Reading from a URL
    """
    myRepository = test1()
    conn = myRepository.getConnection()
    tempAminoFile = "/tmp/myfile.rdf"
    try:
        websource = "http://www.co-ode.org/ontologies/amino-acid/2005/10/11/amino-acid.owl"
        websource = "http://www.ontoknowledge.org/oil/case-studies/CIA-facts.rdf"        
        print "Begin downloading ", websource, " triples ..."
        fname, headers = urllib.urlretrieve(websource, tempAminoFile)
        print "Triples in temp file"
        tempAminoFile = open(fname) 
    except Exception, e:
        print "Failed ", e
    print "Begin loading triples into AG ..."
    conn.add(tempAminoFile)
    print "Loaded ", conn.size(None), " triples."
    if True:
        outputFile = "/users/bmacgregor/Desktop/ciafactbook.nt"
        print "Saving to ", outputFile 
        ntriplesWriter = NTriplesWriter(outputFile)
        conn.export(ntriplesWriter, None);   
    count = 0
    print "Retrieving statements ..."
    statements = conn.getStatements(None, None, None, False, None)
    print "Counting statements ..."
    for s in statements:
        count += 1
        if (count % 50) == 0:  print '.',
    print "Counted %i statements" % count
   
if __name__ == '__main__':
    choices = [i for i in range(9)]
    choices = [10]
    for choice in choices:
        print "\n==========================================================================="
        print "Test Run Number ", choice, "\n"
        if choice == 0: test0()
        elif choice == 1: test1()
        elif choice == 2: test2()
        elif choice == 3: test3()
        elif choice == 4: test4()    
        elif choice == 5: test5()        
        elif choice == 6: test6()            
        elif choice == 7: test7()                
        elif choice == 8: test8()                
        elif choice == 9: test9()                        
        elif choice == 10: test10()                            
        elif choice == 11: test11()                                    
    