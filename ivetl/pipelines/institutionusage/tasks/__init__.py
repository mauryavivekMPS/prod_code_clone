from ivetl.pipelines.institutionusage.tasks.get_jr3_files import GetJR3Files
from ivetl.pipelines.institutionusage.tasks.get_jr2_files import GetJR2Files
from ivetl.pipelines.institutionusage.tasks.validate_jr3_files import ValidateJR3Files
from ivetl.pipelines.institutionusage.tasks.validate_jr2_files import ValidateJR2Files
from ivetl.pipelines.institutionusage.tasks.insert_jr3_into_cassandra import InsertJR3IntoCassandra
from ivetl.pipelines.institutionusage.tasks.insert_jr2_into_cassandra import InsertJR2IntoCassandra