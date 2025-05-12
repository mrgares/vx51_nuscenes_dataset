# Dataset Containers 

## General Architecture Diagram

```mermaid
graph TD
    %% FiftyOne server setup
    subgraph FiftyOne_Server_Container
        A1[FiftyOne App]
        A2[MongoDB Database]
        A1 --> A2
    end

    %% Other containers
    subgraph Other_Containers
        B1[3DGS Container]
        B2[DrivingForward Container]
        B3[Diffusion Model Container]
    end

    %% Shared Docker network
    C[Shared Docker Network: 
    ddgs_network]
    

    %% Communication between containers via shared network
    B1 -->  C
    B2 -->  C
    B3 -->  C

    %% Interaction with FiftyOne app and MongoDB through the network
    C --> |API Calls and Data Transfer| A1
    C --> |Data Stored in MongoDB| A2




```

## Setup

### 1. Create the Docker network (if not already existing)

To allow containers to communicate with each other:

```bash
docker network create dggs_network
```

---

### 2. Build and start the services with Docker Compose

```bash
docker-compose up --build -d
```

This will:

* Start a MongoDB container (`nuscenes_mongo_db`) to store FiftyOne metadata
* Start a developer container (`fiftyone_worker`) with FiftyOne and official plugins
* Mount your datasets and workspace for live development
* Configure dataset downloads to `/datastore/fiftyone`

---

### 3. Connecting Other Containers

Other containers (e.g., for training, analysis, or visualization) can connect to the shared MongoDB using:

```bash
docker run --name <your_container_name> \
  -v $(pwd):/workspace \
  -v /datastore:/datastore \
  --shm-size=16g \
  -it --gpus all \
  --network dggs_network \
  -e FIFTYONE_DATABASE_URI=mongodb://nuscenes_mongo_db:27017 \
  <your_image_name>
```

Replace `<your_container_name>` and `<your_image_name>` with your desired names.
This ensures shared access to datasets and centralized metadata.

