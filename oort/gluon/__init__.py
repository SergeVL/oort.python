# -*- coding: UTF-8 -*-


class Profile(object):
    def __init__(self, source=None):
        source = source['profile'] if 'profile' in source else source
        self.source = source
        self.prefixes = source.get('prefix') or {}
        if 'default' in source:
            self._default_ns = self.prefixes[source.get('default')]
        else:
            self._default_ns = None
        self.parse_definitions(source.get('define'))

    def parse_definitions(self, defs_dict):
        self.definitions = {}
        self._token_uri_map = {}
        self._uri_token_map = {}
        if not defs_dict:
            return
        for token, d_source in defs_dict.items():
            d_map = d_source.copy()
            if 'term' in d_map:
                uri = self.resolve_curie(d_map['term'])
            elif 'from' in d_map:
                uri = self.prefixes[d_map['from']] + token
                d_map['from_ns'] = d_map.pop('from')
            else:
                uri = self._default_ns + token
            dfn = GluonDef(self, token, **d_map)
            self.definitions[uri] = dfn
            self._token_uri_map[dfn.token] = uri
            self._uri_token_map[uri] = dfn.token

    def resolve_curie(self, curie):
        pfx, key = curie.split(':')
        ns = self.prefixes[pfx]
        return ns+key

    def uri_for_key(self, token):
        if token.startswith('$'):
            return token
        elif ':' in token:
            uri = self.resolve_curie(token)
            return uri
        elif token in self._token_uri_map:
            return self._token_uri_map[token]
        elif self._default_ns:
            return self._default_ns + token
        else:
            raise ValueError("Unknown token: %r" % token)

    def token_for_uri(self, uri):
        token = self._uri_token_map.get(uri)
        if not token and self._default_ns and uri.startswith(self._default_ns):
            token = uri[len(self._default_ns):]
        return token


class GluonDef(object):
    def __init__(self, profile, token, term=None, from_ns=None, many=None,
            reference=False, symbol=False, localized=False, datatype=None):
        self._profile = profile
        self.token = token
        self.term = term
        self.from_ns = from_ns
        self.many = many
        self.reference = reference
        self.symbol = symbol
        self.localized = localized
        self.datatype = datatype
    @property
    def datatype_uri(self):
        return self._profile.resolve_curie(self.datatype)


