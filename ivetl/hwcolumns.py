from cassandra.cqlengine.columns import Text

class LowercaseText(Text):
	def to_python(self, value):
		if isinstance(value, str):
			value = value.lower()
		else:
			raise ValidationError("{0} {1} couldn't be treated as str value".format(self, value))
		return self.validate(value)

	def to_database(self, value):
		if isinstance(value, str):
			value = value.lower()
		else:
			raise ValidationError("{0} {1} couldn't be treated as str value".format(self, value))
		return self.validate(value)
