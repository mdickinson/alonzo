# An environment represents a mapping to from Parameter instances to either
# NameExpr instances or Suspension instances.


class UndefinedNameError(Exception):
    """
    Exception raised when trying to resolve a non-existent name.
    """
    pass


class Environment:
    def lookup(self, var):
        """
        Look up a Parameter instance in the current environment.

        Returns either a NameExpr or a Suspension.
        """
        while self:
            if self.var == var:
                return self.val
            self = self.env
        raise UndefinedNameError("Variable not in environment: {}".format(var))

    def lookup_by_name(self, name):
        """
        Look up a name (a string) and recover the corresponding binding
        and value.

        Returns a pair (binding, value).
        """
        while self:
            if self.var.name == name:
                return self.var, self.val
            self = self.env
        raise UndefinedNameError(name)

    def __iter__(self):
        while self:
            var, val, self = self.var, self.val, self.env
            yield var, val

    def append(self, var, val):
        return ChildEnvironment(var, val, self)


class EmptyEnvironment(Environment):
    def __bool__(self):
        return False

    def pop(self):
        raise ValueError("Cannot pop from empty environment")


class ChildEnvironment(Environment):
    def __init__(self, var, val, env):
        """
        Parameters
        ----------
        var : Parameter
        val : NameExpr or Suspension
        env : Environment
        """
        self.var = var
        self.val = val
        self.env = env

    def __bool__(self):
        return True

    def pop(self):
        return self.env


# Constructor function.
environment = EmptyEnvironment
