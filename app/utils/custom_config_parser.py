import re
from io import StringIO

class CustomConfigParser:
    def __init__(self, separator: str = ":=", ignore_lines: list = ["<"]):
        self.config = {}
        self.separator = separator
        self.ignore_lines = ignore_lines
        
    def parse(self, source):
        """Parse depuis un fichier ou une chaîne de caractères"""
        if isinstance(source, str) and '\n' in source:
            return self._parse(StringIO(source))
        with open(source, 'r') as f:
            return self._parse(f)
    
    def _parse(self, file_like):
        for line in file_like:
            line = line.strip()
            if self._should_ignore(line):
                continue
                
            # Séparation clé/valeur avec le séparateur personnalisé
            key_value = line.split(self.separator, 1)
            if len(key_value) != 2:
                continue
                
            key = key_value[0].strip()
            value = key_value[1].strip().rstrip(';')
            
            self._handle_value(key, value)
                
        return self.config
    
    def _should_ignore(self, line: str) -> bool:
        """Vérifie si la ligne doit être ignorée"""
        return any(line.startswith(pattern) for pattern in self.ignore_lines)
    
    def _handle_value(self, key, value):
        """Gestion unique des valeurs (plus de tableau)"""
        try:
            self.config[key] = int(value)
        except ValueError:
            try:
                self.config[key] = float(value)
            except ValueError:
                self.config[key] = value