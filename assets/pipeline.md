
flowchart TD
    classDef stage fill:#f9f,stroke:#333,stroke-width:4px
    classDef component fill:#bbf,stroke:#333,stroke-width:2px
    classDef storage fill:#bfb,stroke:#333,stroke-width:2px
    classDef subcomponent fill:#ffe6cc,stroke:#ff9900,stroke-width:2px

    %% Indexing Stage
    subgraph Indexing["Indexing Stage"]
        direction TB
        A[Document Loader] -->|Load documents| B[Parser]
        B -->|Split into nodes| C[Embedding Model]
        C -->|Generate embeddings| D[Qdrant Vector Store]
        B -->|Store text| E[Redis Document Store]
    end
    class Indexing stage

    %% Qdrant Hybrid Search Component
    subgraph QdrantHybrid["Hybrid Search"]
        direction TB
        Q1[Dense Vector Search] --> Q3[Relative Score Fusion]
        Q2[Sparse Vector Search] --> Q3
        Q3 --> Q4[Top K Nodes]
    end
    class QdrantHybrid component
    class Q1,Q2,Q3,Q4 subcomponent

    %% Generation Stage
    subgraph Generation["Generation Stage"]
        direction TB
        F[Query Input] -->|Embed query| G[Qdrant Hybrid Search]
        G -->|Top K nodes| H[Dense Reranker]
        H -->|Top N nodes| I[LLM]
        E -.->|Fetch relevant text| I
        I -->|Generate response| J[Response]
    end
    class Generation stage

    %% Components
    class A,B,C,F,G,H,I component
    class D,E storage

    %% Interactions between stages
    Indexing -->|Indexed documents| Generation
    G -.->|Use| QdrantHybrid

    %% Color and style
    style Indexing fill:#f0e6ff,stroke:#6600cc
    style Generation fill:#e6f7ff,stroke:#0066cc
    style QdrantHybrid fill:#fff5e6,stroke:#ff9900
    style A fill:#ff9999,stroke:#cc0000
    style B fill:#ffcc99,stroke:#cc6600
    style C fill:#99ccff,stroke:#0066cc
    style D fill:#99ff99,stroke:#009900
    style E fill:#ff99cc,stroke:#cc0066
    style F fill:#ffff99,stroke:#cccc00
    style G fill:#cc99ff,stroke:#6600cc
    style H fill:#ff99ff,stroke:#cc00cc
    style I fill:#99ffff,stroke:#00cccc
    style J fill:#ccffcc,stroke:#00cc66
