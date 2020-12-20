class Base:
    def execute(self, *args, **kwargs):
        raise NotImplementedError(
            'This method should be implemented in the derived class.'
        )
