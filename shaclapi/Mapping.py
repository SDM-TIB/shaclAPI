import copy

class Mapping:
    def __init__(self, tuple) -> None:
        self.bindings = tuple[0]
        self.sn = tuple[1]
        self.exp = tuple[2]

        # Sets to check for duplicates
        self.exp_set = {val_res[0] for val_res in self.exp}
        self.sn_set = {str(tuple) for tuple in self.sn} 

    @property
    def val_report(self):
        return [self.sn, self.exp]

    def __str__(self) -> str:
        return str(self.bindings) + str(self.exp) + str(self.sn)

    '''
    Utility functions to convert between Detrusty representation of URIs and variables and the representation of the API.
    '''    

    def add_var_prefix(self,var):
        '''
        Converts input into a variable starting with ?.
        The internal representation of a variable.
        '''
        var = str(var)
        if var.startswith('?'):
            return var
        else:
            return '?' + var
    
    def del_var_prefix(self,var):
        '''
        Converts input into a variable not starting with ?.
        The external representation of a variable.
        '''
        var = str(var)
        if var.startswith('?'):
            return var[1:]
        else:
            return var
    
    def decapsulate(self,value):
        '''
        Removes leading and subsequent '<' '>'.
        The external representation of a uri.
        '''
        if value.startswith('<') and value.endswith('>'):
            return value[1:-1]
        else: 
            return value
    
    def encapsulate(self,value):
        '''
        Adds leading and subsequent '<' '>'.
        The internal representation of a uri.
        '''
        if value.startswith('http'):
            return '<' + value + '>'
        else:
            return value


    '''
    The following methods are trying to emulate a dictionary type such that one can use Mapping similar to a dictionary.
    The goal is to make as few changes as possible to the operators and at the same time manage the reasoning (sn) and the Validation Results (exp) properly.
    '''

    def __getitem__(self,var):
        var = self.add_var_prefix(var)
        value = self.bindings[var]
        return self.decapsulate(value)
    
    def get(self, var, default):
        var = self.add_var_prefix(var)
        if var in self.bindings:
            return self.decapsulate(self[var])
        else:
            return default
    
    def __setitem__(self,var, value):
        var = self.add_var_prefix(var)
        self.bindings[var] = self.encapsulate(value)
        return self

    def __delitem__(self, var):
        var = self.add_var_prefix(var)
        del self.bindings[var]
        return self
    
    def update(self,mapping2):
        if isinstance(mapping2,Mapping):
            self.bindings.update(mapping2.bindings)

            # Check for duplicates
            for tuple in mapping2.sn:
                if str(tuple) not in self.sn_set:
                    self.sn_set.add(str(tuple))
                    self.sn.append(tuple)
            
            for r in mapping2.exp:
                if r[0] not in self.exp_set:
                    self.exp_set.add(r[0])
                    self.exp.append(r)
        elif isinstance(mapping2, dict):
            self.bindings.update({self.add_var_prefix(key): self.encapsulate(value) for key, value in mapping2.items()})
            #print("Added binding without explaination : " + str(mapping2))
        else:
            raise Exception("Unexpected type to update a Mapping Object: " + str(type(mapping2)))

        # Faster without checking for duplicates
        #self.sn = self.sn + mapping2.sn
        #self.exp = self.exp + mapping2.exp

    def __contains__(self, var):
        var = self.add_var_prefix(var)
        return (var in self.bindings.keys())
    
    def keys(self):
        for key in self.bindings.keys():
            yield self.del_var_prefix(key)
    
    def values(self):
        for value in self.bindings.values():
            yield self.decapsulate(value)

    def items(self):
        for var,value in self.bindings.items():
            yield (self.del_var_prefix(var), self.decapsulate(value))

    def copy(self):
        return Mapping(copy.deepcopy([self.bindings, self.sn, self.exp]))


    '''
    Operator specific functions
    '''
    
    def project(self, vars):
        vars = [self.add_var_prefix(str(var)) for var in vars]
        return Mapping([{key: value for key,value in self.bindings.items() if key in vars}, self.sn, self.exp])
    
