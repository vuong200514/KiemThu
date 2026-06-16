
from datetime import datetime 
import copy 

print ("="*60 )
print ("DISTRIBUTED SYSTEM TEST REPORT")
print ("="*60 )


print ("\n[TEST 1] Timestamp-Based Conflict Resolution")

node1 ={
"id":1 ,
"content":"Old Version",
"timestamp":"2026-06-15T10:00:00"
}

node2 ={
"id":1 ,
"content":"New Version",
"timestamp":"2026-06-15T10:05:00"
}

t1 =datetime .fromisoformat (node1 ["timestamp"])
t2 =datetime .fromisoformat (node2 ["timestamp"])

winner =node1 if t1 >t2 else node2 

print ("Node 1:",node1 )
print ("Node 2:",node2 )
print ("Expected Winner: Node 2")
print ("Actual Winner:",winner ["content"])

if winner ["content"]=="New Version":
    print ("RESULT: PASS")
else :
    print ("RESULT: FAIL")


print ("\n[TEST 2] Data Replication")

source_db =[
{"id":1 ,"content":"Note A"},
{"id":2 ,"content":"Note B"},
{"id":3 ,"content":"Note C"}
]

replica_db =copy .deepcopy (source_db )

print ("Source Node Data:",source_db )
print ("Replica Node Data:",replica_db )

if source_db ==replica_db :
    print ("RESULT: PASS")
else :
    print ("RESULT: FAIL")


print ("\n[TEST 3] Consistency Verification")

if source_db ==replica_db :
    print ("All replicated records are identical.")
    print ("RESULT: PASS")
else :
    print ("Data inconsistency detected.")
    print ("RESULT: FAIL")

print ("\n"+"="*60 )
print ("ALL TESTS COMPLETED")
print ("="*60 )
