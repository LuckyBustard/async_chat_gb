class CantCreateException(Exception):
    def __init__(self):
        self.text = 'Нельзя создавать эксземпляры этого класса'

    def __str__(self):
        return self.text