conn = new Mongo();
db = conn.getDB("ticket_test");

print(tojson(db.sport.deleteMany({})))
print(tojson(db.sport.insertOne({item: "badminton", 'day': NumberInt(2), 'time': [['11:30', '13:30']]})))
print(tojson(db.sport.insertOne({item: "badminton", 'day': NumberInt(4), 'time': [['17:00', '20:00']]})))
print(tojson(db.sport.insertOne({item: "badminton", 'day': NumberInt(5), 'time': [['11:30', '13:30']]})))
print(tojson(db.sport.insertOne({item: "basketball", 'day': NumberInt(2), 'time': [['11:30', '13:30']]})))
print(tojson(db.sport.insertOne({item: "basketball", 'day': NumberInt(4), 'time': [['11:30', '13:30']]})))
print(tojson(db.sport.insertOne({item: "yoga", 'day': NumberInt(4), 'time': [['11:30', '13:30']]})))
print(tojson(db.sport.insertOne({item: "swim", 'day': NumberInt(3), 'time': [['11:30', '13:30']]})))
print(tojson(db.sport.insertOne({item: "swim", 'day': NumberInt(5), 'time': [['11:30', '13:30']]})))
print(tojson(db.sport.insertOne({item: "football", 'day': NumberInt(1), 'time': [['11:30', '13:30']]})))
print(tojson(db.sport.insertOne({item: "football", 'day': NumberInt(3), 'time': [['11:30', '13:30']]})))
