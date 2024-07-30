graph TB

%% Classes for styling
classDef user fill:#6C8EBF,stroke:#5A7AA5,color:#FFF,rx:5,ry:5
classDef tenant fill:#B8E986,stroke:#97C665,color:#333,rx:5,ry:5
classDef pipeline fill:#FFB570,stroke:#D99559,color:#333,rx:5,ry:5
classDef database fill:#FF9999,stroke:#E57373,color:#333,rx:10,ry:10
classDef index fill:#DDA0DD,stroke:#BA55D3,color:#333,rx:5,ry:5
classDef filter fill:#87CEFA,stroke:#4682B4,color:#333,rx:5,ry:5
classDef legend fill:#F0F0F0,stroke:#D3D3D3,color:#333,rx:5,ry:5

subgraph SingleTenancy["Single Tenancy"]
    U1[Alice]:::user
    U2[Bob]:::user
    P1[Pipeline]:::pipeline
    P2[Pipeline]:::pipeline
    DB1[(Qdrant Collection<br>All Libraries)]:::database
    I1{{Vector Store Index}}:::index
    
    U1 --> P1
    U2 --> P2
    P1 & P2 --> DB1
    P1 & P2 -.-> I1
    I1 -.-> DB1
end

subgraph MultiTenancy["Multi-Tenancy"]
    U3[Carol]:::user
    U4[David]:::user
    T1[LlamaIndex Docs]:::tenant
    T2[Qdrant Docs]:::tenant
    P3[Pipeline]:::pipeline
    P4[Pipeline]:::pipeline
    DB2[(Qdrant Collection<br>with Payload Index)]:::database
    I2{{Vector Store Index}}:::index
    F1{Filter: library=llama-index}:::filter
    F2{Filter: library=qdrant}:::filter
    
    U3 --> T1 --> P3
    U4 --> T2 --> P4
    P3 --> F1
    P4 --> F2
    F1 & F2 --> DB2
    P3 & P4 -.-> I2
    I2 -.-> DB2
end

%% Styling
style SingleTenancy fill:#E6F3FF,stroke:#B3D9FF,stroke-width:2px,rx:10,ry:10
style MultiTenancy fill:#F0FFF0,stroke:#C1E1C1,stroke-width:2px,rx:10,ry:10

%% Annotations
SingleTenancy -.- ST["• All users access all library docs<br>• No data isolation<br>• Global search across all docs"]
MultiTenancy -.- MT["• Users access only specific library docs<br>• Data isolation via filters<br>• Efficient search within each library"]

%% Layout
SingleTenancy ~~~ MultiTenancy
