# 📖 Data Dictionary

## Biodiversity & Native Planting Planner

Primary application datasets:

```text
data/processed/plants_app.csv
data/processed/plant_states.csv
```

## Plant Identification

| Field | Description |
|---|---|
| `plant_id` | Identifier used to connect plant records |
| `display_name` | Plant name displayed by the application |
| `common_name` | Common plant name |
| `scientific_name` | Scientific botanical name |
| `plant_family` | Botanical family |
| `plant_type` | General plant type |

## Sunlight

| Field | Description |
|---|---|
| `supports_full_sun` | Full-sun suitability |
| `supports_part_shade` | Part-shade suitability |
| `supports_shade` | Shade suitability |

## Water

| Field | Description |
|---|---|
| `supports_low_water` | Low-water suitability |
| `supports_medium_water` | Medium-water suitability |
| `supports_high_water` | High-water suitability |

## Pollinators

| Field | Description |
|---|---|
| `supports_bee_observed` | Bee interaction observed |
| `supports_butterfly_observed` | Butterfly interaction observed |
| `supports_hummingbird_observed` | Hummingbird interaction observed |
| `supports_moth_observed` | Moth interaction observed |
| `supports_fly_observed` | Fly interaction observed |
| `supports_beetle_observed` | Beetle interaction observed |
| `supports_wasp_observed` | Wasp interaction observed |

## Soil

| Field | Description |
|---|---|
| `soil_description` | Suitable soil description |
| `soil_moisture` | Preferred soil moisture |
| `soil_ph` | Soil pH information |

## Maintenance and Climate

| Field | Description |
|---|---|
| `maintenance` | Plant maintenance requirement |
| `zone_min` | Minimum hardiness zone |
| `zone_max` | Maximum hardiness zone |

## Bloom

| Field | Description |
|---|---|
| `bloom_color` | Recorded bloom colors |
| `bloom_jan` through `bloom_dec` | Monthly bloom indicators |

## Images

| Field | Description |
|---|---|
| `image_url` | Plant image URL |
| `image_source` | Image source |

## State Dataset

### `plant_states.csv`

| Field | Description |
|---|---|
| `plant_id` | Plant identifier |
| `native_state` | U.S. state associated with native distribution |

## Recommendation Fields

```text
plant_id
supports_full_sun
supports_part_shade
supports_shade
supports_low_water
supports_medium_water
supports_high_water
supports_bee_observed
supports_butterfly_observed
supports_hummingbird_observed
supports_moth_observed
supports_fly_observed
supports_beetle_observed
supports_wasp_observed
```

## Dataset Relationship

```text
plants_app.csv
      │
      │ plant_id
      ▼
plant_states.csv
      │
      ▼
Native State Relationship
```
