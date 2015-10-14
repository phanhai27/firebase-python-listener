from firebase_streaming import Firebase

# Sample callback function
def p(x):
    print x

# Firebase object
fb = Firebase('https://myfirebase.firebaseio.com/')

# Add listener to colors child with no callback
no_callback = fb.child("colors").listener()

# Or use a custom callback
custom_callback = fb.child("shapes").listener(p)

# Start and stop the stream using the following
custom_callack.start()
raw_input("ENTER to stop...")
custom_callback.stop()
