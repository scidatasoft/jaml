import mongoengine
from mongoengine import Document, StringField, ReferenceField, ListField, EmbeddedDocument, IntField, DictField, \
    EmbeddedDocumentListField, FileField, EmbeddedDocumentField, ObjectIdField, FloatField, BooleanField, \
    EmailField


class Config(Document):
    """ Various system configuration properties """

    name = StringField(required=True)

    settings = DictField()


class Role(Document):
    """ Secure entity in the system """

    name = StringField(required=True, unique=True)

    description = StringField()

    privileges = ListField(StringField())
    "List of system-wide privileges"


class Group(Document):
    """ Secure entity in the system """

    name = StringField(required=True, unique=True)

    description = StringField()

    privileges = ListField(StringField())
    "List of system-wide privileges"

    roles = ListField(StringField())
    "List of group's roles"


class User(Document):
    """ Secure entity in the system """

    username = StringField(required=True, unique=True)

    password_hash = StringField(required=True)

    full_name = StringField()

    email = EmailField(required=True, unique=True)

    company = StringField()

    privileges = ListField(StringField())
    "List of directly assigned system-wide privileges"

    roles = ListField(StringField())
    "List of user's roles"

    groups = ListField(StringField())
    "List of user's groups"

    active = BooleanField(default=True)


class Session(Document):
    """ User's session """

    user = ReferenceField(User, reverse_delete_rule=mongoengine.CASCADE)

    privileges = ListField(StringField())
    "List of privileges composed at login time from a combination of user's and role's privileges"

    active = BooleanField(default=True)


class ACL(EmbeddedDocument):
    """ Object's access rights """

    access = StringField(required=True, default='public')
    "public, authenticated, private"

    owner = StringField(required=True)

    read = ListField(StringField())

    write = ListField(StringField())


class Molecule(Document):
    """A single-component unique chemical structure derendundified by InChIKey"""

    inchi_key = StringField(required=True, unique=True)
    "InChIKey"

    inchi = StringField(required=True, unique=True)
    "InChI"

    names = ListField(StringField())
    "Chemical names"

    mol = StringField(required=True)
    "MOL"


class StructureRecord(EmbeddedDocument):
    """Represents a set of records from original file"""

    # TODO required=True, unique=True
    ord = IntField()
    "Record ordinal within file"

    fields = DictField()
    "Field values"

    molecule = ReferenceField(Molecule)
    "Reference to a structure object"


class SDF(Document):
    """Structures Definition File (SDF) - represents an original file (CSV or SDF)"""

    name = StringField(required=True)
    "File name including extension"

    size = IntField()
    "File size in bytes"

    metadata = DictField()
    "Various additional information"

    fields = ListField(StringField())
    "List of all fields in the original file (e.g. CSV columns or SDF fields)"

    fields_mapping = ListField(DictField())
    "Original to semantic fields mappings"

    records_number = IntField()
    "Number of records in the original file"

    records = EmbeddedDocumentListField(StructureRecord)
    "Reference to structure record objects which were InChI-fied"

    file = FileField()
    "Original file (SDF, CSV, XLSX)"

    acl = EmbeddedDocumentField(ACL)
    "Access rights to this document"


class DatasetCompound(EmbeddedDocument):
    """Chemical structure with activity - ready for modeling"""

    ord = IntField(required=True)
    "Compound ordinal within a dataset"

    fields = DictField()
    "Semantically named fields set"

    molecule = ReferenceField(Molecule, required=True)
    "RDKit MOL object - standardized chemical representation"


class Issue(EmbeddedDocument):
    severity = StringField(required=True)

    message = StringField(required=True)


class StdizerRecord(EmbeddedDocument):
    """Single record issues"""

    file = ReferenceField(SDF, required=True)
    "File the record came from"

    ord = IntField(required=True)
    "Compound ordinal within file"

    file_fields = DictField()
    "File record fields"

    ds_fields = DictField()
    "Dataset record fields"

    issues = EmbeddedDocumentListField(Issue)
    "Issues identified during standardization"

    mol_org = ReferenceField(Molecule)
    "Original molecule"

    mol_std = ReferenceField(Molecule)
    "Standardized molecule"


class Protocol(Document):
    """Log of all found issues for a given dataset"""

    name = StringField(required=True)
    "Standardizer type (e.g. Simple or EPA)"

    records = EmbeddedDocumentListField(StdizerRecord)

    records_number = IntField()


class Dataset(Document):
    """Modeling set - combines Compounds"""

    name = StringField(required=True)
    "Dataset name"

    metadata = DictField()
    "A (possibly modified) copy of SDF metadata"

    protocol = ReferenceField(Protocol, reverse_delete_rule=mongoengine.CASCADE)
    "Conversion protocol from SDF to Dataset - e.g. the standardizer choice"

    stats = DictField()
    "Various stats about this dataset"

    fields_mapping = ListField(DictField())
    "Original to semantic fields mappings, by default a copy from SDF"

    records_number = IntField()
    "Number of records in dataset"

    records = EmbeddedDocumentListField(DatasetCompound)
    "MongoDB compound object reference"

    files = ListField(ReferenceField(SDF, reverse_delete_rule=mongoengine.CASCADE))

    acl = EmbeddedDocumentField(ACL)
    "Access rights to this document"


class Descriptors(EmbeddedDocument):
    provider = StringField()
    "Library/provider (e.g. PaDEL, RDKit, TEST, Mordred, etc)"

    name = StringField(required=True)
    "Descriptors type (e.g. ECFP, FCFP)"

    params = DictField()
    "E.g. radius = 3 (ECFP6)"


class Blob(Document):
    """ Images, reports, etc """

    params = DictField()
    "Various context-dependent options (e.g. kind, name, description, etc)"

    file = FileField(required=True)
    "Image or file body as bytes"


class Model(Document):
    name = StringField(required=True, unique_with='method_name')
    "Model name - matches dataset name"

    method_name = StringField(required=True)
    "Abbreviated method name (e.g. knn, nb, ada)"

    label = StringField()

    descriptors = EmbeddedDocumentListField(Descriptors)
    "Descriptors"

    test_set_size = IntField()
    train_indices = ListField(IntField())
    test_indices = ListField(IntField())

    params = DictField()
    "Method hyper-parameters - specific to the method"

    architecture = StringField()
    "DNN model architecture"

    metrics = DictField()
    "Internal and External metrics - internal X-validation"

    images = ListField(ReferenceField(Blob))
    "Model images and reports - e.g. ROC"

    model = FileField()
    "Serialized model's binary"

    execution_time = FloatField()
    "Time in seconds the model building has taken"

    dataset = ReferenceField(Dataset, reverse_delete_rule=mongoengine.CASCADE)

    acl = EmbeddedDocumentField(ACL)
    "Access rights to this document"


class Prediction(EmbeddedDocument):
    value = FloatField(required=True)
    "Predicted value"

    applicability = FloatField()
    "Applicability Domain"

    error = FloatField()
    "Error in prediction"


class MoleculePredictions(EmbeddedDocument):
    """Chemical structure with activity - ready for modeling"""

    db_id = StringField(required=True)
    "Compound ID within a dataset"

    molecule = ReferenceField(Molecule, required=True)
    "RDKit MOL object - standardized chemical representation"

    predictions = EmbeddedDocumentListField(Prediction)
    "Model-value tuples"


class ModelPredictions(Document):
    model = ReferenceField(Model, required=True)
    "Model"

    predictions = EmbeddedDocumentListField(MoleculePredictions)
    "Molecule-Model-Value tuples"


class ValidationStats(EmbeddedDocument):
    model = StringField()

    img_id = ObjectIdField()

    metrics = DictField()


class ResultSet(Document):
    name = StringField(required=True)

    metadata = DictField()
    "A (possibly modified) copy of SDF metadata"

    protocol = ReferenceField(Protocol, reverse_delete_rule=mongoengine.CASCADE)
    "Conversion protocol from SDF to Dataset - e.g. the standardizer choice"

    stats = DictField()
    "Various stats about this dataset"

    fields_mapping = ListField(DictField())
    "Original to semantic fields mappings, by default a copy from SDF"

    records_number = IntField()
    "Number of records in dataset"

    records = EmbeddedDocumentListField(DatasetCompound)
    "MongoDB compound object reference"

    files = ListField(ReferenceField(SDF, reverse_delete_rule=mongoengine.CASCADE))
    "References to files from which this resultset was composed"

    models = ListField(ReferenceField(Model, reverse_delete_rule=mongoengine.CASCADE))

    valid_stats = EmbeddedDocumentListField(ValidationStats)

    acl = EmbeddedDocumentField(ACL)
    "Access rights to this document"


class JobInfo(Document):
    job_type = StringField(required=True)
    "Job status"

    server_name = StringField()

    container_name = StringField()

    params = DictField()

    status = StringField(required=True)
    "Job status"

    stdout = StringField()

    stderr = StringField()

    error = StringField()
    "Error if any"

    stack_trace = StringField()
    "Error stack trace"

    stats = DictField()
    "Various job stats"

    model_id = StringField()

    acl = EmbeddedDocumentField(ACL)
    "Access rights to this document"
