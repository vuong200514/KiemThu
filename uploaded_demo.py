from tinydb import TinyDB ,Query 

db =TinyDB ('db.json')

db .insert ({
'name':'Alice',
'age':20 
})

db .insert ({
'name':'Bob',
'age':22 
})

User =Query ()

result =db .search (User .age >20 )

print (result )