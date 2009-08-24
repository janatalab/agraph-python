import time, cjson, math
from request import *

class Catalog:
    def __init__(self, url, user=None, password=None):
        self.url = url
        self.user = user
        self.password = password

    def listRepositories(self):
        """Returns the names of repositories in the catalog."""
        repos = jsonRequest(self, "GET", "/repositories")
        return [repo["id"] for repo in repos]

    def createRepository(self, name):
        """Ask the server to create a new repository."""
        nullRequest(self, "PUT", "/repositories/" + urllib.quote(name))
        return self.getRepository(name)

    def deleteRepository(self, name):
        """Delete a repository in this catalog."""
        nullRequest(self, "DELETE", "/repositories/" + urllib.quote(name))

    # def federateTripleStores(self, name, storeNames):
    #     """Create a federated store."""
    #     nullRequest(self, "PUT", "/repositories/" + urllib.quote(name) +
    #                 "?" + urlenc(federate=storeNames))

    def getRepository(self, name):
        """Create an access object for a triple store."""
        return Repository(self.url + "/repositories/" + urllib.quote(name), self.user, self.password)


class Client(Catalog):
    def listCatalogs(self):
        return [cat["id"] for cat in jsonRequest(self, "GET", "/catalogs")]

    def openCatalog(self, uriOrName):
        if (uriOrName.startswith("http://")):
            return Catalog(uriOrName, self.user, self.password)
        else:
            return self.openCatalogByName(uriOrName);

    def openCatalogByName(self, name=None):
        url = self.url
        if name and name != "~":
            url += "/catalogs/" + urllib.quote(name)
        return self.openCatalog(url)


class Repository:
    def __init__(self, url, user=None, password=None):
        # TODO verify existence of repository at this point?
        self.url = url
        self.user = user
        self.password = password

    def getSize(self, context=None):
        """Returns the amount of triples in the repository."""
        return jsonRequest(self, "GET", "/size", urlenc(context=context))

    def listContexts(self):
        """Lists the contexts (named graphs) that are present in this repository."""
        return [t["contextID"] for t in jsonRequest(self, "GET", "/contexts")]

    def evalSparqlQuery(self, query, infer=False, context=None, namedContext=None, callback=None,
                        bindings=None, planner=None, checkVariables=None):
        """Execute a SPARQL query. Context can be None or a list of
        contexts -- strings in "http://foo.com" form or "null" for the
        default context. Return type depends on the query type. ASK
        gives a boolean, SELECT a {names, values} object containing
        lists of lists of terms. CONSTRUCT and DESCRIBE return a list
        of lists representing statements. Callback WILL NOT work on
        ASK queries."""
        if (bindings is not None):
            bindings = "".join(["&$" + urllib.quote(a) + "=" + urllib.quote(b.encode("utf-8")) for a, b in bindings.items()])
        return jsonRequest(self, "GET", self.url,
                           urlenc(query=query, infer=infer, context=context, namedContext=namedContext,
                                  planner=planner, checkVariables=checkVariables) + (bindings or ""),
                           rowreader=callback and RowReader(callback))

    def evalPrologQuery(self, query, infer=False, callback=None, limit=None):
        """Execute a Prolog query. Returns a {names, values} object."""
        return jsonRequest(self, "POST", self.url,
                           urlenc(query=query, infer=infer, queryLn="prolog", limit=limit),
                           rowreader=callback and RowReader(callback))

    def definePrologFunctors(self, definitions):
        """Add Prolog functors to the environment. Takes a string
        containing Lisp-syntax functor definitions (using the <-- and
        <- operators)."""
        nullRequest(self, "POST", "/functor", definitions)

    def evalInServer(self, code):
        """Evaluate Common Lisp code in the server."""
        return jsonRequest(self, "POST", "/eval", code)

    def getStatements(self, subj=None, pred=None, obj=None, context=None, infer=False, callback=None, limit=None, tripleIDs=False):
        """Retrieve all statements matching the given constraints.
        Context can be None or a list of contexts, as in
        evalSparqlQuery."""
        if subj == [] or pred == [] or obj == [] or context == []: return []
        subjEnd, predEnd, objEnd = None, None, None
        if isinstance(subj, tuple): subj, subjEnd = subj
        if isinstance(pred, tuple): pred, predEnd = pred
        if isinstance(obj, tuple): obj, objEnd = obj
        return jsonRequest(self, "GET", "/statements",
                           urlenc(subj=subj, subjEnd=subjEnd, pred=pred, predEnd=predEnd,
                                  obj=obj, objEnd=objEnd, context=context, infer=infer, limit=limit),
                           rowreader=callback and RowReader(callback),
                           accept=(tripleIDs and "application/x-quints+json") or "application/json")

    def addStatement(self, subj, pred, obj, context=None):
        """Add a single statement to the repository."""
        ##print "ADD STATEMENT CONTEXT '%s' " % context, type(context)
        nullRequest(self, "POST", "/statements", cjson.encode([[subj, pred, obj, context]]),
                    contentType="application/json")

    def deleteMatchingStatements(self, subj=None, pred=None, obj=None, context=None):
        """Delete all statements matching the constraints from the
        repository. Context can be None or a single graph name."""
        nullRequest(self, "DELETE", "/statements",
                    urlenc(subj=subj, pred=pred, obj=obj, context=context))

    def addStatements(self, quads):
        """Add a collection of statements to the repository. Quads
        should be an array of four-element arrays, where the fourth
        element, the graph name, may be None."""
        nullRequest(self, "POST", "/statements", cjson.encode(quads), contentType="application/json")

    class UnsupportedFormatError(Exception):
        def __init__(self, format): self.format = format
        def __str__(self): return "'%s' file format not supported (try 'ntriples' or 'rdf/xml')." % self.format

    def checkFormat(self, format):
        if format == "ntriples": return "text/plain"
        elif format == "rdf/xml": return "application/rdf+xml"
        else: raise Repository.UnsupportedFormatError(format)

    def loadData(self, data, format, baseURI=None, context=None):
        nullRequest(self, "POST", "/statements?" + urlenc(context=context, baseURI=baseURI),
                    data.encode("utf-8"), contentType=self.checkFormat(format))

    def loadFile(self, file, format, baseURI=None, context=None, serverSide=False):
        mime = self.checkFormat(format)
        body = ""
        if not serverSide:
            f = open(file)
            body = f.read()
            f.close()
            file = None
        params = urlenc(file=file, context=context, baseURI=baseURI)
        nullRequest(self, "POST", "/statements?" + params, body, contentType=mime)

    def getBlankNodes(self, amount=1):
        return jsonRequest(self, "POST", "/blankNodes", urlenc(amount=amount))

    def deleteStatements(self, quads):
        """Delete a collection of statements from the repository."""
        nullRequest(self, "POST", "/statements/delete", cjson.encode(quads), contentType="application/json")

    def deleteStatementsById(self, ids):
        nullRequest(self, "POST", "/statements/delete?ids=true", cjson.encode(ids), contentType="application/json")

    def evalFreeTextSearch(self, pattern, infer=False, callback=None, limit=None):
        """Use free-text indices to search for the given pattern.
        Returns an array of statements."""
        return jsonRequest(self, "GET", "/freetext", urlenc(pattern=pattern, infer=infer, limit=limit),
                           rowreader=callback and RowReader(callback))

    def listFreeTextPredicates(self):
        """List the predicates that are used for free-text indexing."""
        return jsonRequest(self, "GET", "/freetext/predicates")

    def registerFreeTextPredicate(self, predicate):
        """Add a predicate for free-text indexing."""
        nullRequest(self, "POST", "/freetext/predicates", urlenc(predicate=predicate))

    def clearNamespaces(self):
        nullRequest(self, "DELETE", "/namespaces")

    def addNamespace(self, prefix, uri):
        nullRequest(self, "PUT", "/namespaces/" + urllib.quote(prefix),
                    uri, contentType="text/plain")

    def deleteNamespace(self, prefix):
        nullRequest(self, "DELETE", "/namespaces/" + urllib.quote(prefix))

    def listMappedTypes(self):
        return jsonRequest(self, "GET", "/mapping/type")

    def addMappedType(self, type, primitiveType):
        nullRequest(self, "POST", "/mapping/type", urlenc(type=type, primitiveType=primitiveType))

    def deleteMappedType(self, type):
        nullRequest(self, "DELETE", "/mapping/type", urlenc(type=type))

    def listMappedPredicates(self):
        return jsonRequest(self, "GET", "/mapping/predicate")

    def addMappedPredicate(self, predicate, primitiveType):
        nullRequest(self, "POST", "/mapping/predicate",
                    urlenc(predicate=predicate, primitiveType=primitiveType))

    def deleteMappedPredicate(self, predicate):
        nullRequest(self, "DELETE", "/mapping/predicate", urlenc(predicate=predicate))

    def getCartesianGeoType(self, stripWidth, xMin, xMax, yMin, yMax):
        """Retrieve a cartesian geo-spatial literal type."""
        return jsonRequest(self, "POST", "/geo/types/cartesian?" +
                           urlenc(stripWidth=stripWidth, xmin=xMin, ymin=yMin, xmax=xMax, ymax=yMax))


    def getSphericalGeoType(self, stripWidth, unit="degree", latMin=None, latMax=None, longMin=None, longMax=None):
        """Retrieve a spherical geo-spatial literal type."""
        return jsonRequest(self, "POST", "/geo/types/spherical?" +
                           urlenc(stripWidth=stripWidth, unit=unit, latmin=latMin, latmax=latMax,
                                  longmin=longMin, longmax=longMax))

    def listGeoTypes(self):
        """List the geo-spatial types registered in the store."""
        return jsonRequest(self, "GET", "/geo/types")

    def createCartesianGeoLiteral(self, type, x, y):
        """Create a geo-spatial literal of the given type."""
        return "\"%+g%+g\"^^<%s>" % (x, y, type)

    class UnsupportedUnitError(Exception):
        def __init__(self, unit): self.unit = unit
        def __str__(self): return "'%s' is not a known unit (use km, mile, degree, or radian)." % self.unit

    def unitDegreeFactor(self, unit):
        if unit == "degree": return 1.0
        elif unit == "radian": return 57.29577951308232
        elif unit == "km": return 0.008998159
        elif unit == "mile": return 0.014481134
        else: raise Repository.UnsupportedUnitError(unit)

    def createSphericalGeoLiteral(self, type, lat, long, unit="degree"):
        """Create a geo-spatial latitude/longitude literal of the
        given type. Unit can be 'km', 'mile', 'radian', or 'degree'."""
        def asISO6709(number, digits):
            sign = "+"
            if (number < 0):
                sign= "-"
                number = -number;
            fl = math.floor(number)
            return sign + (("%%0%dd" % digits) % fl) + (".%07d" % ((number - fl) * 10000000))

        conv = self.unitDegreeFactor(unit)
        return "\"%s%s\"^^<%s>" % (asISO6709(lat * conv, 2), asISO6709(long * conv, 3), type)

    def getStatementsHaversine(self, type, predicate, lat, long, radius, unit="km", limit=None):
        """Get all the triples with a given predicate whose object
        lies within radius units from the given latitude/longitude."""
        return jsonRequest(self, "GET", "/geo/haversine",
                           urlenc(type=type, predicate=predicate, lat=lat, long=long, radius=radius, unit=unit, limit=limit))

    def getStatementsInsideBox(self, type, predicate, xMin, xMax, yMin, yMax, limit=None):
        """Get all the triples with a given predicate whose object
        lies within the specified box."""
        return jsonRequest(self, "GET", "/geo/box",
                           urlenc(type=type, predicate=predicate, xmin=xMin, xmax=xMax, ymin=yMin, ymax=yMax, limit=limit))

    def getStatementsInsideCircle(self, type, predicate, x, y, radius, limit=None):
        """Get all the triples with a given predicate whose object
        lies within the specified circle."""
        return jsonRequest(self, "GET", "/geo/circle",
                           urlenc(type=type, predicate=predicate, x=x, y=y, radius=radius, limit=limit))

    def getStatementsInsidePolygon(self, type, predicate, polygon, limit=None):
        """Get all the triples with a given predicate whose object
        lies within the specified polygon (see createPolygon)."""
        return jsonRequest(self, "GET", "/geo/polygon",
                           urlenc(type=type, predicate=predicate, polygon=polygon, limit=limit))

    def createPolygon(self, resource, points):
        """Create a polygon with the given name in the store. points
        should be a list of literals created with createCartesianGeoLiteral."""
        nullRequest(self, "PUT", "/geo/polygon?" +
                    urlenc(resource=resource, point=points))