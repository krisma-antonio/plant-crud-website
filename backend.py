import sqlite3
from flask import Flask
from flask import g
from flask import render_template
from flask import request

app = Flask(__name__)
DATABASE = 'catalog.db'

# routes
@app.route("/")
def plant_index():
    plants = query_db('SELECT * FROM PLANT')
    return render_template('mainPlantPage.html.j2', plants=plants)

# read plant
@app.route("/view/<int:plant_id>")
def plant_view(plant_id):
    plant = get_single_plant(plant_id)
    if plant:
        return render_template('viewPlant.html.j2', 
                id=plant['PLANT_ID'],
                common=plant['COMMON'], 
                botanical=plant['BOTANICAL'], 
                zone=plant['ZONE'],
                light=plant['LIGHT'],
                price=plant['PRICE'],
                availability=plant['AVAILABILITY'])
    else:
        plants = query_db('SELECT * FROM PLANT')
        return render_template('mainPlantPage.html.j2', plants=plants)

# create new plant
@app.route("/create", methods=['GET','POST'])
def plant_create():
    if request.method == 'GET':
        return render_template('createPlant.html.j2')
    elif request.method == 'POST':
        common = request.form['common']
        botanical = request.form['botanical']
        zone = int(request.form['zone'])
        light = request.form['light']
        price = float(request.form['price'])
        availability = request.form['availability']

        errors = plant_verify(common, botanical, zone, light, price, availability)
        if errors:
            return render_template('createPlant.html.j2', 
                common=common, 
                botanical=botanical,
                zone=zone,
                light=light,
                price=price,
                availability=availability,
                errors=errors)
        else:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(('INSERT INTO PLANT(COMMON, BOTANICAL, ZONE, LIGHT, PRICE, AVAILABILITY) VALUES (?, ?, ?, ?, ?, ?)'), (common, botanical, zone, light, price, availability))
            conn.commit()
            plants = query_db('SELECT * FROM PLANT')
            return render_template('mainPlantPage.html.j2', plants=plants, added=common)

# delete plant
@app.route("/delete/<int:plant_id>", methods=['GET'])
def plant_delete(plant_id):
    plant = get_single_plant(plant_id)
    if plant:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(('DELETE FROM PLANT WHERE PLANT_ID = ?'), (plant_id,))
        conn.commit()
        plants = query_db('SELECT * FROM PLANT')
        return render_template('mainPlantPage.html.j2', plants=plants, deleted=plant['COMMON'])

# edit plant
@app.route("/edit/<int:plant_id>", methods=['GET','POST'])
def plant_edit(plant_id):
    if request.method == 'GET':
        plant = get_single_plant(plant_id)
        if plant:
            return render_template('editPlant.html.j2', 
                    id=plant['PLANT_ID'],
                    common=plant['COMMON'], 
                    botanical=plant['BOTANICAL'], 
                    zone=plant['ZONE'],
                    light=plant['LIGHT'],
                    price=plant['PRICE'],
                    availability=plant['AVAILABILITY'])
        else:
            plants = query_db('SELECT * FROM PLANT')
            return render_template('mainPlantPage.html.j2', plants=plants, errors=['Invalid common plant'])
    elif request.method == 'POST':
        common = request.form['common']
        botanical = request.form['botanical']
        zone = int(request.form['zone'])
        light = request.form['light']
        price = float(request.form['price'])
        availability = request.form['availability']
        errors = plant_verify(common, botanical, zone, light, price, availability)
        if errors:
            return render_template('editPlant.html.j2', 
                id=plant_id,
                common=common, 
                botanical=botanical,
                zone=zone,
                light=light,
                price=price,
                availability=availability,
                errors=errors)
        else:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(('UPDATE PLANT SET COMMON = ?, BOTANICAL = ?, ZONE = ?, LIGHT = ?, PRICE = ?, AVAILABILITY = ? WHERE PLANT_ID =' + str(plant_id)), 
                (common, botanical, zone, light, price, availability))
            conn.commit()
            plants = query_db('SELECT * FROM PLANT')
            return render_template('mainPlantPage.html.j2', plants=plants, updated=common)

# helper functions
def plant_verify(common, botanical, zone, light, price, availability):
    errors = []

    if zone > 13 or zone < 0:
        errors.append('Invalid zone, must be an integer between 0-13. 0 is for annual.')

    return errors

# database stuff
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
        
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('plants.schema', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        
def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def get_single_plant(plant_id):
    plant = query_db('SELECT * FROM PLANT WHERE PLANT_ID = ' + str(plant_id))
    if plant:
        return plant[0]
    else:
        return None 