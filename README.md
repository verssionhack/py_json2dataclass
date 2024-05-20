# Usage

./parse_json2dataclass.py <json_path>

# Example

There is a jsonfile pathed '/home/user/student.json' which content is:

{"name": "bob", "age": 16}

Run command `./parse_json2dataclass.py /home/user/student.json:studnet` and it will create a new file named student.py which content is:

```python

@dataclass
class Student:
  name: str
  age: int

  def __init__(self, data: dict):
      self.name = data.get('name')
      self.age = data.get('age')

```
