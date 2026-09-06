import os
import re
from pathlib import Path
from pydoc import locate
from tkinter import EventType

from flask import Blueprint, jsonify, render_template, request
from werkzeug.utils import secure_filename

from lib import Config
from lib.repositories import PollinatorRepository, EvidenceTypeRepository, StateRepository, CountyRepository, \
    PlantRepository, LocateRepository

web_routes = Blueprint('web',__name__)

@web_routes.get('/import')
def import_data():
    return render_template("import.html")


@web_routes.get('/')
def home():
    states = StateRepository.get_all()
    counties = CountyRepository.get_all()
    pollinators = PollinatorRepository.get_all()
    return render_template("index.html", states=states, counties=counties, pollinators=pollinators)


@web_routes.route('/upload', methods=['POST'])
def upload_file():
    # 1. Check if the file part is even in the request
    if 'file' not in request.files:
        return 'No file part in the request', 400

    file = request.files['file']

    # 2. Check if the user submitted an empty form without selecting a file
    if file.filename == '':
        return 'No file selected', 400

    # secure_filename prevents directory traversal attacks (e.g., ../../etc/passwd)
    filename = secure_filename(file.filename)
    destination_path = os.path.join(Config.UPLOAD_FOLDER, filename)

    file.save(destination_path)
    data = []
    with open(destination_path, 'r',encoding = "utf-8") as file:
        data = file.read().splitlines()
        print(data[:1])
    data_body = data[1:]
    index_scientific_name = 0
    index_species = 1
    index_family = 2
    index_genus = 3
    index_county = 4
    index_state = 5
    index_latitude = 6
    index_longitude = 7
    index_event_date = 8
    index_year = 9
    index_target_taxon_name = 10
    index_interaction_type = 11
    index_pollinator_group = 12
    index_evidence_type = 13

    counter = 0
    print(len(data_body))
    for item in data_body:
       data_item = item.split(',')
       pollinator_name = data_item[index_pollinator_group]
       pollinator_name = pollinator_name.strip().lower()
       pollinator = PollinatorRepository.get_by_name(pollinator_name)
       if not pollinator:
           pollinator = PollinatorRepository.create({
               "name": pollinator_name,
           })
       evidence_type_name = data_item[index_evidence_type]
       evidence_type_name = evidence_type_name.strip().lower()
       evidence_type = EvidenceTypeRepository.get_by_name(evidence_type_name)
       if not evidence_type:
           evidence_type = EvidenceTypeRepository.create({
               "name": evidence_type_name,
           })

       state_name = data_item[index_state]
       state_name = state_name.strip().lower()
       state = StateRepository.get_by_name(state_name)
       if not state:
           state = StateRepository.create({
               "name": state_name,
           })

       county_name = data_item[index_county]
       county_name = county_name.strip().lower()
       county = CountyRepository.get_by_name(county_name)
       if not county:
           county = CountyRepository.create({
               "name": county_name,
               "stateId": state.id,
           })

       plant_name = data_item[index_scientific_name]
       plant_name = plant_name.strip().lower()
       plant = PlantRepository.get_by_name(plant_name)
       if not plant:
           plant = PlantRepository.create({
               "pollinatorId": pollinator.id,
               "evidenceTypeId": evidence_type.id,
               "scientificName": plant_name,
               "species": data_item[index_species].strip().lower(),
               "family": data_item[index_family].strip().lower(),
               "genus": data_item[index_genus].strip().lower(),
               "targetTaxonName": data_item[index_target_taxon_name].strip(),
               "eventDate": data_item[index_event_date].strip(),
               "lat": data_item[index_latitude].strip(),
               "long": data_item[index_longitude].strip(),
           })

       locates = LocateRepository.get_all(state_id=state.id,county_id=county.id,plant_id=plant.id)
       locate = locates[0] if len(locates) > 0 else None
       if not locate:
           locate = LocateRepository.create({
               "stateId": state.id,
               "countyId": county.id,
               "plantId": plant.id,
           })

       counter += 1

    Path(destination_path).unlink()
    return render_template("upload.html", import_count=counter)

@web_routes.route('/search', methods=['POST'])
def search():
    stateId = request.form.get('state')
    countyId = request.form.get('county')
    pollinatorId = request.form.get('pollinator')

    plant_pollinators = PlantRepository.get_all(pollinator_id=int(pollinatorId))
    plants = []
    for plant in plant_pollinators:
        locates = LocateRepository.get_all(plant_id=int(plant.id), state_id=int(stateId), county_id=int(countyId))
        if locates is not None and len(locates) > 0:
            plant.image_url = slug(plant.scientificName)
            plant.image_url = plant.image_url + ".jpg"
            plants.append(plant)
    return render_template("result.html", plants=plants)

def slug(name):
    """'Claytonia perfoliata subsp. perfoliata' -> 'Claytonia_perfoliata_subspperfoliata'"""
    return re.sub(r"[^A-Za-z0-9]+", "_", name.capitalize()).strip("_")