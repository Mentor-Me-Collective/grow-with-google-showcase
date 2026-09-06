from datetime import datetime
from typing import Any
from sqlalchemy.exc import IntegrityError


from lib.extensions import db
from lib.models import Plant, plant


class PlantRepository(object):
    @staticmethod
    def get_all(evidence_type_id: int|None = None, pollinator_id: int|None = None) -> list[Plant]:
        query = Plant.query
        if evidence_type_id is not None:
            query = query.filter(Plant.evidenceTypeId ==  evidence_type_id)
        if pollinator_id is not None:
            query = query.filter(Plant.pollinatorId == pollinator_id)
        return query.order_by(Plant.scientificName.asc()).all()

    @staticmethod
    def get_by_name(scientific_name: str) -> Plant | None:
        return Plant.query.filter(Plant.scientificName == scientific_name).first()

    @staticmethod
    def get_by_id(plant_id: int) -> Plant | None:
        return Plant.query.get(plant_id)

    @staticmethod
    def create(data: dict[str, Any]) -> Plant:
        pollinator_id= int(data.get('pollinatorId', 0))
        if pollinator_id == 0:
            raise ValueError("Pollinator id is required")
        evidence_type_id = int(data.get('evidenceTypeId', 0))
        if evidence_type_id  == 0:
            raise ValueError("evidence type id is required")
        scientific_name = str(data.get('scientificName', "")).strip()
        if not scientific_name:
            raise ValueError("Scientific name  is required")
        species = str(data.get('species', "")).strip()
        if not species:
            raise ValueError("Species name  is required")
        family = str(data.get('family', "")).strip()
        if not family:
            raise ValueError("Family name  is required")
        genus = data.get('species', "")
        if not genus :
            raise ValueError("genus name  is required")
        target_taxon_name = str(data.get('targetTaxonName', "")).strip()
        if not target_taxon_name:
            raise ValueError("Target taxon name  is required")
        event_date= str(data.get('eventDate', "")).strip()
        if not event_date:
            raise ValueError("Date is required")
        event_date = datetime.strptime(event_date, "%Y-%m-%d").date()
        latitude = float(data.get('lat', 0))
        if latitude == 0:
            raise ValueError("latitude is required")
        longitude = float(data.get('long', 0))
        if longitude == 0:
            raise ValueError("longitude is required")

        plant = Plant(pollinatorId=pollinator_id, evidenceTypeId=evidence_type_id,
                      scientificName=scientific_name, species=species, family=family, genus=genus,
                      targetTaxonName=target_taxon_name,eventDate=event_date, lat=latitude,long=longitude)

        try:
            db.session.add(plant)
            db.session.commit()
        except IntegrityError as error:
            db.session.rollback()
            raise ValueError("Plant already exists")
        return plant

    @staticmethod
    def update(plant: Plant, data: dict[str, Any]) -> Plant:
        name = data.get('name')
        if not name:
            raise ValueError("Name is required")
        pollinator_id = int(data.get('pollinatorId', 0))
        if pollinator_id == 0:
            raise ValueError("Pollinator id is required")
        evidence_type_id = int(data.get('evidenceTypeId', 0))
        if evidence_type_id == 0:
            raise ValueError("evidence type id is required")
        scientific_name = str(data.get('scientificName', "")).strip()
        if not scientific_name:
            raise ValueError("Scientific name  is required")
        species = str(data.get('species', "")).strip()
        if not species:
            raise ValueError("Species name  is required")
        family = str(data.get('family', "")).strip()
        if not family:
            raise ValueError("Family name  is required")
        genus = str(data.get('species', "")).strip()
        if not genus:
            raise ValueError("genus name  is required")
        target_taxon_name = str(data.get('targetTaxonName', "")).strip()
        if not target_taxon_name:
            raise ValueError("Target taxon name  is required")
        event_date = str(data.get('eventDate', "")).strip()
        if not event_date:
            raise ValueError("Date is required")
        event_date = datetime.strptime(event_date, "%Y-%m-%d").date()
        latitude = float(data.get('lat', 0))
        if latitude == 0:
            raise ValueError("latitude is required")
        longitude = float(data.get('long', 0))
        if longitude == 0:
            raise ValueError("longitude is required")
        plant.name = name
        plant.pollinatorId = pollinator_id
        plant.evidenceTypeId = evidence_type_id
        plant.scientificName=scientific_name
        plant.species=species
        plant.family=family
        plant.genus=genus
        plant.targetTaxonName=target_taxon_name
        plant.eventDate=event_date
        plant.lat=latitude
        plant.long=longitude
        try:
            db.session.commit()
        except IntegrityError as error:
            db.session.rollback()
            raise ValueError("Plant already exists")
        return plant

    @staticmethod
    def delete(plant: Plant) -> None:
        db.session.delete(plant)
        db.session.commit()

