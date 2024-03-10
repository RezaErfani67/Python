
def start_mongod():
   
    process1 = subprocess.Popen(
        ['mongod' , '--port' , '27019' , '--dbpath' , 'c:\data\db'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


    time.sleep(3)

    process2 = subprocess.Popen(
        ['mongo' , '--port' ,'27019'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    process2.stdin.write('use admin;\n'.encode())
    # process1.stdin.close()  # Close stdin to signal end of input

    
    for line in process1.stdout:
        print(line.decode().strip())
    for line in process1.stderr:
        print(line.decode().strip())


    for line in process2.stdout:
        print(line.decode().strip())
    for line in process2.stderr:
        print(line.decode().strip())

    # Wait for the process to finish
    process1.wait()
    process2.wait()
    
    print("mongod process exited with return code:", process1.returncode)

# 1- start process async on main thread
# start_mongod()

# 2- start process on new thread
# Start the mongod process in a new thread
# mongod_thread = threading.Thread(target=start_mongod)
# mongod_thread.start()


3- start process on new thread
with ThreadPoolExecutor(max_workers=1) as executor:
    future = executor.submit(start_mongod)



print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
print("=====================================")
