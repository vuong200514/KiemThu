from datetime import datetime 
import copy 



# Tóm tắt: Không có docstring cho resolve_conflict
def resolve_conflict (note_a ,note_b ):
    time_a =datetime .fromisoformat (note_a ["timestamp"])
    time_b =datetime .fromisoformat (note_b ["timestamp"])
    return note_a if time_a >time_b else note_b 



# Tóm tắt: Không có docstring cho test_conflict_resolution
def test_conflict_resolution ():
    node1_note ={
    "id":1 ,
    "content":"Hello from Node 1",
    "timestamp":"2026-06-15T10:00:00"
    }

    node2_note ={
    "id":1 ,
    "content":"Updated from Node 2",
    "timestamp":"2026-06-15T10:05:00"
    }

    winner =resolve_conflict (node1_note ,node2_note )

    print ("===== CONFLICT RESOLUTION TEST =====")
    print ("Winner:",winner )



# Tóm tắt: Không có docstring cho test_replication
def test_replication ():
    node1_db =[
    {"id":1 ,"content":"Note A"},
    {"id":2 ,"content":"Note B"}
    ]

    node2_db =copy .deepcopy (node1_db )

    print ("\n===== REPLICATION TEST =====")
    print ("Node1:",node1_db )
    print ("Node2:",node2_db )

if __name__ =="__main__":
    test_conflict_resolution ()
    test_replication ()
