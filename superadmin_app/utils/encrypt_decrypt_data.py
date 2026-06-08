from django.db import models
from django.conf import settings
from datetime import datetime, date


def encrypt_value(value):
    if not value:
        return value
    try:
        return settings.FERNET.encrypt(value.encode()).decode()
    except Exception as e:
        print(f"Encryption error: {e}")
        return value

def decrypt_value(value):
    if not value:
        return value
    try:
        return settings.FERNET.decrypt(value.encode()).decode()
    except Exception:
        return value



class EncryptedTextField(models.TextField):
    """Automatically encrypt/decrypt text values."""

    def from_db_value(self, value, expression, connection):
        return decrypt_value(value)

    def get_prep_value(self, value):
        return encrypt_value(value)


class EncryptedCharField(models.CharField):
    """Encrypt/decrypt short text (CharField) values."""

    def from_db_value(self, value, expression, connection):
        return decrypt_value(value)

    def get_prep_value(self, value):
        return encrypt_value(value)


class EncryptedURLField(models.URLField):
    """Encrypt/decrypt URLs."""

    def from_db_value(self, value, expression, connection):
        return decrypt_value(value)

    def get_prep_value(self, value):
        return encrypt_value(value)




class EncryptedDateField(models.Field):
    """Encrypt/decrypt date values, stored as text in the DB."""
    description = "Encrypted date stored as text"

    def get_internal_type(self):
        return "TextField"  # Database stores text

    def from_db_value(self, value, expression, connection):
        if not value:
            return None
        decrypted = decrypt_value(value)
        if decrypted:
            try:
                return datetime.fromisoformat(decrypted).date()
            except Exception:
                return None
        return None

    def to_python(self, value):
        if isinstance(value, date):
            return value
        if not value:
            return None
        decrypted = decrypt_value(value)
        if decrypted:
            try:
                return datetime.fromisoformat(decrypted).date()
            except Exception:
                return None
        return None

    def get_prep_value(self, value):
        if not value:
            return None
        if isinstance(value, date):
            value = value.isoformat()
        return encrypt_value(value)


class EncryptedDateTimeField(models.Field):
    """Encrypt/decrypt datetime values, stored as text in the DB."""
    description = "Encrypted datetime stored as text"

    def __init__(self, *args, **kwargs):
        self.auto_now = kwargs.pop('auto_now', False)
        self.auto_now_add = kwargs.pop('auto_now_add', False)
        super().__init__(*args, **kwargs)

    def get_internal_type(self):
        return "TextField"

    def pre_save(self, model_instance, add):
        """
        Automatically set current datetime if auto_now or auto_now_add is used.
        """
        if self.auto_now or (self.auto_now_add and add):
            value = datetime.now()
            setattr(model_instance, self.attname, value)
            return value
        return getattr(model_instance, self.attname)

    def from_db_value(self, value, expression, connection):
        if not value:
            return None
        decrypted = decrypt_value(value)
        try:
            return datetime.fromisoformat(decrypted)
        except Exception:
            return None

    def to_python(self, value):
        if isinstance(value, datetime):
            return value
        if not value:
            return None
        decrypted = decrypt_value(value)
        try:
            return datetime.fromisoformat(decrypted)
        except Exception:
            return None

    def get_prep_value(self, value):
        if not value:
            return None
        if isinstance(value, datetime):
            value = value.isoformat()
        return encrypt_value(value)


class EncryptedDecimalField(models.DecimalField):
    """Encrypt/decrypt decimal values as strings."""

    def from_db_value(self, value, expression, connection):
        decrypted = decrypt_value(value)
        if decrypted:
            return decrypted
        return None

    def get_prep_value(self, value):
        if value is not None:
            return encrypt_value(str(value))
        return None
    
    
    
    
class EncryptedImageField(models.ImageField):
    """
    Custom ImageField that encrypts/decrypts only the file path string.
    Does NOT encrypt the image binary data.
    """

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return decrypt_value(value)

    def to_python(self, value):
        # When Django loads a model, value may already be decrypted or a File object.
        if value and isinstance(value, str):
            try:
                return decrypt_value(value)
            except Exception:
                return value
        return value

    def get_prep_value(self, value):
        if not value:
            return value

        # Handle File object case (extract name before encryption)
        if hasattr(value, "name"):
            value = value.name

        return encrypt_value(value)
        
        
        
class EncryptedEmailField(models.EmailField):
    """Encrypt/decrypt email addresses."""

    def from_db_value(self, value, expression, connection):
        return decrypt_value(value)

    def get_prep_value(self, value):
        return encrypt_value(value)            