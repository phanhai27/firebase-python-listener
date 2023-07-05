import json
from firebase_streaming import Firebase

# Sample callback function
def p(x):
    print('------------')
    print(x.timestamp)
    print(x.notif)
    print(x.admin_id)


with open('firebase_info.json') as user_file:
  file_contents = user_file.read()
  
print(file_contents)
parsed_json = json.loads(file_contents)

# Firebase object
fb = Firebase(parsed_json['root_url'])

# Use a custom callback\
callback = fb.child(parsed_json['child_path'] + "/" + parsed_json['agent_id']).listener(p)

# Start and stop the stream using the following
callback.start()
input("ENTER to stop...\n")
callback.stop()
