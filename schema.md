# Schema and backend routes

#### Property Table
    id: int (PK)
    url: string (unique, the source listing link)
    address: string
    description: text
    created_at: datetime
    updated_at: datetime

#### Photo Table
    id: int (PK)
    property_id: int (FK → Property.id)
    url: string (location of the photo)
    room_type: string (nullable, filled after classification)

#### Renovation Table
    id: int (PK)
    property_id: int (FK → Property.id)
    bathroom: boolean
    kitchen: boolean
    living_room: boolean
    bedroom: boolean
    basement: boolean


## Backend Routes

### Property Intake
- **POST /properties/intake**
  - Body: `{ "url": "<property_url>" }`
  - Response:  
    ```json
    {
      "id": 123,
      "address": "...",
      "description": "...",
      "photos": ["..."]
    }
    ```

### Renovation Extraction
- **POST /properties/{id}/renovations**
  - Body: `{ "description": "..." }`
  - Response:  
    ```json
    { "bathroom": true, "kitchen": false }
    ```

### Photo Classification
- **POST /properties/{id}/photos/classify**
  - Body: `{ "photos": ["url1", "url2"] }`
  - Response:  
    ```json
    {
      "photo1.jpg": "bathroom",
      "photo2.jpg": "kitchen"
    }
    ```

### Database Lookup
- **GET /properties/{id}**
  - Response: cached results for that property

### Extra Utility Routes
- **GET /properties**
  - Response: list of all stored properties

- **DELETE /properties/{id}**
  - Response: confirmation of deletion
