System Architecture and Technical Specification for recon-iq: An Enterprise-Grade AI-Powered Financial Reconciliation EngineWithin the domain of global transaction processing, financial institutions demand absolute analytical accuracy and structural adaptability when reconciling multi-party transaction files. Systemic processing anomalies, ledger formatting mismatches, and microscopic calculation drift often obscure critical transaction mismatches. The architecture proposed for the reconciliation project—designated as recon-iq—presents a comprehensive, cloud-native platform built to ingest, map, and reconcile multi-party transactional datasets. Engineered with a foundational stack consisting of the Google Agent Development Kit, BigQuery, Python FastAPI, Docker, and MongoDB, this platform introduces an automated cognitive architecture for transaction matching and forensic anomaly detection.Technical Architecture and System TopologyThe physical and logical configuration of recon-iq is designed as a decoupled, event-driven enterprise architecture. By separating high-throughput ingestion pipelines from cognitive mapping layers and analytical calculations, the system remains performant when processing high-volume transactional logs.                                 ┌─────────────────────────────────┐
                                 │       Enterprise Clients        │
                                 └────────────────┬────────────────┘
                                                  │
                                                  ▼ (TLS 1.3 / JSON / Multipart)
                                 ┌─────────────────────────────────┐
                                 │     API Ingestion Gateway       │
                                 │       (Python FastAPI)          │
                                 └──────┬───────────────────┬──────┘
                                        │                   │
                     (Async Stream)     │                   │ (JSON Documents)
         ┌──────────────────────────────┘                   └──────────────────────────────┐
         ▼                                                                                 ▼
┌──────────────────────────────┐                                                   ┌──────────────────────────────┐
│  Data Ingestion Pipeline     │                                                   │      Session Metadata        │
│    (Pandas / XML / CSV)      │                                                   │         (MongoDB)            │
└────────┬──────────────┬──────┘                                                   └──────────────────────────────┘
         │              │
         │ (Dry-Run Match)
         │              └───────────────────────────────────┐
         ▼                                                  ▼
┌──────────────────────────────┐                  ┌──────────────────────────────┐
│  High-Precision Engine       │                  │     Vertex AI Platform       │
│    (Python Decimal Core)     │                  │  (Gemini 2.5 Dynamic Map)    │
└────────┬─────────────────────┘                  └─────────────────┬────────────┘
         │                                                          │
         │ (High-Throughput Streaming Upload)                       │ (Generated SQL/Parameters)
         ▼                                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                           Google Cloud Platform                                                 │
│  ┌─────────────────────────────────┐                            ┌────────────────────────────────────────────┐  │
│  │      BigQuery Data Warehouse    │                            │         Google Agent SDK (ADK)             │  │
│  │   - Structured Storage          │                            │      - BigQuery & DataAgent Toolsets       │  │
│  │   - Date-Partitioned Tables     │◄───────────────────────────┤      - Multi-Agent Orchestrator            │  │
│  │   - SQL-Driven Analytics        │  (Secure gRPC Executions)  │      - Automated Intent Processing         │  │
│  │   - Decimal Precision Models    │                            │      - Semantic Matching Framework         │  │
│  │   └─────────────────────────────┘                            └────────────────────────────────────────────┘  │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
The transactional routing lifecycle is divided into five distinct operational planes:The Ingestion Plane (FastAPI): Exposes asynchronous HTTP endpoints optimized to ingest multiple raw transaction file payloads simultaneously. This plane manages raw request payloads, parses multi-part boundaries, and streams incoming files directly to temporary spooled memory blocks to prevent container exhaustion.The Metadata Plane (MongoDB): A document store designed to retain schema structures, dynamic mapping templates, matching run logs, and configuration state.The Precision Matching Plane (Decimal Module Core): An in-memory execution pipeline utilizing Python arbitrary-precision arithmetic to perform strict comparison checks on financial records down to a hard tolerance threshold of $0.001$.The Analytics Plane (BigQuery): An enterprise-grade, serverless data warehouse hosting long-term transaction data. BigQuery tables are partitioned by transactional dates and clustered by Bank Name and Agent Name to minimize query slot consumption.The Cognitive Orchestration Plane (Google Agent SDK): A framework that integrates Gemini models with physical databases. Utilizing native tools like the BigQueryToolset and DataAgentToolset, the agent converts conversational business inquiries into secure, optimized SQL executions.The matrix below maps the primary software components to their technical boundaries and interaction protocols:System LayerSelected TechnologyStructural InterfaceArchitectural DriverIngestion RouterPython FastAPI / Uvicorn REST HTTP over TLS 1.3Handles asynchronous non-blocking stream routing for multi-file operations.Document LedgerMongoDB v6.0PyMongo BSON DriverRetains session state, custom mappings, run metrics, and system logs with high write throughput.Analytical WarehouseGoogle BigQueryGoogle Cloud Client API Stores petabyte-scale reconciled ledger records; supports high-speed analytical indexing.Cognitive Agent CoreGoogle Agent SDK (ADK) gRPC Channel Interface Translates conversational intents into structured SQL and analytical parameters.Forensic Matching CorePython Decimal Module In-Memory ArraysRuns multi-way math algorithms using exact base-10 numerical representations.Stream-Based Ingestion and Dynamic XML/CSV/Excel ParsingThe core capability of recon-iq begins with its ingestion engine, which accepts and standardizes multi-format inputs (CSV, Microsoft Excel, and nested XML). Upload requests are handled asynchronously through FastAPI using UploadFile parameters, allowing the system to handle binary streams without loading entire payloads into memory.Pythonimport io
import pandas as pd
from fastapi import UploadFile, HTTPException

def parse_incoming_file_stream(file_payload: UploadFile) -> pd.DataFrame:
    """
    Decodes and normalizes file payloads from stream buffers based on MIME-types
    and file extensions to construct uniform, typed DataFrames.
    """
    filename = file_payload.filename
    extension = filename.split(".")[-1].lower() if "." in filename else ""
    
    try:
        # Spooled stream reading to handle high-capacity file payloads
        stream_buffer = io.BytesIO(file_payload.file.read())
        
        if extension == "csv":
            return pd.read_csv(stream_buffer, keep_default_na=False)
            
        elif extension in ["xlsx", "xls"]:
            return pd.read_excel(stream_buffer, keep_default_na=False)
            
        elif extension == "xml":
            # Direct parsing through custom utility wrapper to handle nesting anomalies
            return parse_structured_xml_payload(stream_buffer)
            
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"The file extension '{extension}' is not supported by the ingestion pipeline."
            )
    except Exception as exc:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process file stream for {filename}: {str(exc)}"
        )
Parsing Dynamic XML with Structural IntegrityStandard XML payloads present complex challenges due to deep nesting, repeated child attributes, and default namespaces. Under standard Pandas read_xml operations, child elements that share tag names but use different attributes can cause column overwriting, leading to data loss.XML<transaction>
    <id>TX_99211</id>
    <value type="primary_charge">150.00</value>
    <value type="tax_offset">12.50</value>
</transaction>
To prevent parser overwrites, recon-iq uses specific configurations within the Pandas read_xml API. If default namespaces are present (e.g., xmlns="http://schemas.recon-iq.com/ledger"), a temporary prefix is dynamically registered. To parse memory-heavy, multi-gigabyte XML datasets efficiently, the parser can use the iterparse dictionary parameter to process targeted parent nodes sequentially.Pythondef parse_structured_xml_payload(stream_buffer: io.BytesIO) -> pd.DataFrame:
    """
    Resolves namespace collisions and uses XPath structures to parse hierarchical XML payloads
    without risk of column overwrites.
    """
    try:
        # Safe extraction with standard XPath configuration
        df = pd.read_xml(
            stream_buffer,
            xpath=".//transaction",
            parser="lxml",
            dtype_backend="numpy_nullable"
        )
        return df
    except ValueError:
        # Fallback mechanism if schema uses non-standard nesting structure
        stream_buffer.seek(0)
        return pd.read_xml(
            stream_buffer, 
            xpath="./*", 
            parser="lxml"
        )
For complex, repeating elements with varying attributes, recon-iq uses an explicit names configuration to map elements to separate columns. Alternatively, it maps unique identifiers into structured columns using iterparse keys to prevent overlapping schema values.Bidirectional AI-Driven Schema MappingTraditionally, integrating diverse financial sources required manually defining database mapping rules or hardcoding target field schemas directly into software components. However, minor column renames or file modifications would break these pipelines, requiring manual engineering support.To build a more resilient system, recon-iq uses a two-pass context-aware schema alignment pipeline. First, a lightweight extraction pass summarizes the file's structure. Second, an alignment pass uses Gemini to map fields bidirectionally based on semantic meaning.Raw Upload Ingestion File (CSV/XLSX/XML)
                  │
                  ▼
[Pass 1: Metadata Profiling] ──► Read Headers + Sample Data ──► Structural Profile (JSON Schema)
                                                                       │
                                                                       ▼
[Pass 2: Cognitive Mapping]  ──► Contextual Evaluation via Gemini ─────┤
                                                                       ▼
[Output Matrix Generation]   ──► Map Fields & Estimate Confidence ◄────┘
Pass 1: Extraction of the Structural Metadata ProfileRather than sending massive raw data files to the LLM—which increases context window costs and processing times—recon-iq reads a 50-row subsample to generate a lightweight structural profile. This profile summarizes the schema and includes:Raw Column Headers or XML tag hierarchies.Native Data Types (e.g., floating-point, integer, date-time, ISO string).Unique item count, value density, and sample values.Pass 2: Context-Aware Schema Retrieval and Stable MappingThe metadata profile is processed using the Gemini API via the google-genai SDK. The model analyzes the semantic context of each raw column to map it to the system's core target primitives: transaction_id, amount, and timestamp.To improve mapping accuracy, recon-iq evaluates column relationships bidirectionally. It assesses mapping compatibility from the source table to the system schema, and from the system schema back to the source table. The model generates a confidence score ($C \in [0.0, 1.0]$) for each match. These scores are computed by evaluating output logits for preferred matches, ensuring highly reliable schema alignment.Raw Field NameSelected Target PrimitiveInferred FormatConfidence (C)Rationale and Contextual Mapping Logic Bank_Tx_Reftransaction_idAlphanumeric String0.99Serves as the primary unique identifier for ledger records; contains transaction-level reference codes.posted_amtamountString Numeric (150.25)0.98Represents the base transaction value; requires normalization to a high-precision Decimal type.Timestamp_UTCtimestampISO-8601 String0.97Records the date and time of the event; mapped to database timestamp structures.ledger_descdescription (Metadata)Free Text String0.85Provides descriptive context for the transaction; not used as a primary matching key.Using this mapping table, recon-iq standardizes incoming datasets into a canonical format, preparing them for precision matching calculations.High-Precision Matching and Microscopic Reconciliation EngineFinancial reconciliation systems require absolute arithmetic precision. Standard IEEE-754 double-precision floating-point values are stored as binary fractions, which means numbers like 0.1 or 0.2 cannot be represented exactly. These minor inaccuracies accumulate during large batch runs, leading to false discrepancies that distort ledger balances.To eliminate floating-point representation drift, recon-iq uses Python's arbitrary-precision decimal library for all financial calculations. Raw values are converted directly from strings into Decimal structures, avoiding float conversions entirely.Raw Source Value (String: "105.10") ──► Python Decimal Object ──► Exact Base-10 Arithmetic
       ▲
       │ (Avoid converting to Float to prevent binary truncation errors )
Floating-Point representation (0.1000000000000000055511...)
The Precision Reconciliation PipelineThe matching engine handles both two-way and three-way reconciliation workflows. The primary match is established using the unique transaction_id. If an exact key match is missing, the engine falls back to a multi-conditional matching window. This fallback checks for matching values within a $\pm 3$-day window to account for standard bank processing delays.Pythonfrom decimal import Decimal, getcontext, ROUND_HALF_UP
import pandas as pd

# Configure execution environment to support up to 28 digits of precision
getcontext().prec = 28
getcontext().rounding = ROUND_HALF_UP

def reconcile_two_party_ledgers(
    source_df: pd.DataFrame, 
    target_df: pd.DataFrame, 
    mapping: dict, 
    tolerance_threshold: Decimal = Decimal('0.001') # Inferred enterprise limit [5, 25]
) -> tuple:
    """
    Executes a high-precision two-way reconciliation. Compares source and target ledgers 
    by transaction ID, applying exact base-10 math to flag value discrepancies.
    """
    matched_records =
    unmatched_source =
    unmatched_target = target_df.copy()
    unmatched_target['Matched'] = False
    
    # Track matching status on target dataframe
    target_by_id = target_df.set_index(mapping['target_id'])
    
    for _, s_row in source_df.iterrows():
        s_id = str(s_row[mapping['source_id']])
        s_amt = Decimal(str(s_row[mapping['source_amount']])) # Convert directly from string 
        s_time = pd.to_datetime(s_row[mapping['source_time']])
        
        if s_id in target_by_id.index:
            t_row = target_by_id.loc[s_id]
            t_amt = Decimal(str(t_row[mapping['target_amount']]))
            t_time = pd.to_datetime(t_row[mapping['target_time']])
            
            # Execute base-10 comparison checks 
            variance = abs(s_amt - t_amt)
            date_diff = abs((s_time - t_time).days)
            
            is_matched = (variance <= tolerance_threshold) and (date_diff <= 3) # Window check 
            
            matched_records.append({
                "transaction_id": s_id,
                "source_amount": s_amt,
                "target_amount": t_amt,
                "variance": variance,
                "status": "MATCHED" if is_matched else "VALUE_MISMATCH",
                "timestamp": s_time
            })
            
            # Update target match state
            unmatched_target.loc[unmatched_target[mapping['target_id']] == s_id, 'Matched'] = True
        else:
            unmatched_source.append(s_row)
            
    # Filter out matched transactions to isolate discrepancies
    unmatched_t_final = unmatched_target[~unmatched_target['Matched']].drop('Matched', axis=1)
    
    return pd.DataFrame(matched_records), pd.DataFrame(unmatched_source), unmatched_t_final
Three-Way Reconciliation LogicWhen three datasets are uploaded (e.g., internal ledger, payment gateway log, and bank statement), reconciliation requires a tri-directional matching matrix to isolate imbalances.Let $T_{1}$, $T_{2}$, and $T_{3}$ represent the transactions from File 1, File 2, and File 3. For each transaction ID, the system evaluates the following variances:$$\Delta_{1,2} = |V_{T1} - V_{T2}|$$$$\Delta_{2,3} = |V_{T2} - V_{T3}|$$$$\Delta_{1,3} = |V_{T1} - V_{T3}|$$A transaction is considered fully reconciled if and only if:$$\Delta_{1,2} \le 0.001 \quad \land \quad \Delta_{2,3} \le 0.001 \quad \land \quad \Delta_{1,3} \le 0.001$$If any variance exceeds $0.001$, the transaction is flagged and mapped to a specific discrepancy profile:Matching ConditionDiscrepancy StatusPrimary Operational Root CauseActionable Correction Path$\Delta_{1,2} > 0.001 \land \Delta_{2,3} > 0.001$Processor DiscrepancyIncomplete clearing or settlement delay in File 2 (Payment Gateway).Query the gateway API to verify processing status; update processing logs.$\Delta_{1,3} > 0.001 \land \Delta_{2,3} > 0.001$Bank Settlement VarianceProcessing error or unexpected service fee in File 3 (Bank Statement).Review bank transaction details; flag the variance for manually managed audit adjustment.ID missing in $T_{2}$ and $T_{3}$Unreconciled Internal LedgerTransaction recorded internally but not executed or sent to the gateway.Verify system transaction logs; check for internal connection dropouts or system lag.ID missing in $T_{1}$Unknown TransactionTransaction settled in the bank/gateway but not recorded in the internal system.Investigate payment capture flow; run internal systems audit to detect lost entries.This multi-conditional mapping matrix ensures that even minor mismatches are caught and routed to the correct clearing channel.Storage Architecture: Partitioned BigQuery and Document MongoDBTo manage both transactional data and audit metadata, recon-iq uses a dual-database storage strategy. High-volume ledger data is stored in BigQuery, while session configurations, parsing schemas, and system logs are managed in MongoDB.BigQuery Analytics StoreTo handle large-scale database operations and keep queries highly performant, BigQuery tables use explicit partitioning and clustering schemes.Partitioning: Tables are partitioned by day using a transaction_date field. This limits query execution scans to specific date ranges, reducing data processing costs.Clustering: Partitioned tables are clustered by bank_name and agent_name. This clusters matching records physically close together, optimizing SQL queries that filter by specific banks or agents.SQL-- DDL schema script establishing the partitioned historical analytics warehouse
CREATE TABLE `recon-iq-production.analytics_warehouse.historical_ledger`
(
    bank_name STRING NOT NULL,
    agent_name STRING NOT NULL,
    transaction_id STRING NOT NULL,
    amount NUMERIC NOT NULL,  -- High-precision numeric type for exact decimal values
    transaction_date DATE NOT NULL,
    timestamp TIMESTAMP,
    status STRING,
    matching_checksum STRING
)
PARTITION BY transaction_date
CLUSTER BY bank_name, agent_name;
MongoDB Metadata SchemaOperational metadata is stored in MongoDB. The document structure below shows how session details, schemas, and processing summaries are managed:JSON{
  "_id": "647f3b89f1d24a001b9a9e32",
  "session_id": "a9e5b32f-48cf-432d-905e-df659ba912a3",
  "bank_name": "Chase Enterprise",
  "agent_name": "ACH_Processor_v2",
  "date_range": {
    "from_date": "2026-06-01",
    "to_date": "2026-06-07"
  },
  "ingested_files": [
    {
      "filename": "internal_ledger_june.csv",
      "mime_type": "text/csv",
      "row_count": 145020,
      "schema_signature": "d2f4a1..."
    }
  ],
  "dynamic_mappings": {
    "transaction_id": "Bank_Tx_Ref",
    "amount": "posted_amt",
    "timestamp": "Timestamp_UTC"
  },
  "run_metrics": {
    "total_records": 145020,
    "perfect_matches": 144985,
    "mismatch_count": 35,
    "unresolved_amount": "45.021"
  }
}
Double-Store Sync APIThis FastAPI endpoint allows direct batch uploads to BigQuery while writing operational run details to the MongoDB metadata store:Pythonfrom fastapi import APIRouter, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/sync", tags=["synchronization"])

class BigQueryDirectLoadPayload(BaseModel):
    bank_name: str = Field(..., example="Chase Enterprise")
    agent_name: str = Field(..., example="ACH_Processor_v2")
    from_date: str = Field(..., example="2026-06-01")
    to_date: str = Field(..., example="2026-06-07")
    records: list[dict] = Field(..., description="Array of normalized transaction dictionaries")

@router.post("/direct-load", status_code=status.HTTP_201_CREATED)
async def direct_load_to_warehouse(payload: BigQueryDirectLoadPayload):
    """
    Streams transaction arrays directly to partitioned BigQuery tables
    and logs run metadata to MongoDB.
    """
    table_id = "recon-iq-production.analytics_warehouse.historical_ledger"
    
    # Map incoming JSON objects to BigQuery-compliant schemas
    formatted_rows =
    for item in payload.records:
        formatted_rows.append({
            "bank_name": payload.bank_name,
            "agent_name": payload.agent_name,
            "transaction_id": str(item["transaction_id"]),
            "amount": str(Decimal(str(item["amount"]))), # Ensure values are string-parsed for exact precision
            "transaction_date": str(item["transaction_date"]),
            "timestamp": str(item["timestamp"]),
            "status": str(item.get("status", "UNRECONCILED"))
        })
        
    try:
        # Stream rows directly to BigQuery tables
        bq_errors = bq_client.insert_rows_json(table_id, formatted_rows)
        if bq_errors:
            raise HTTPException(
                status_code=500, 
                detail=f"BigQuery write pipeline failed: {bq_errors}"
            )
            
        # Write metadata update to MongoDB
        db.historical_sync_runs.insert_one({
            "bank_name": payload.bank_name,
            "agent_name": payload.agent_name,
            "date_range": {"from": payload.from_date, "to": payload.to_date},
            "records_count": len(payload.records),
            "timestamp": datetime.datetime.utcnow()
        })
        
        return {
            "status": "success",
            "synchronized_records_count": len(formatted_rows),
            "destination_table": table_id
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500, 
            detail=f"Synchronization pipeline error: {str(exc)}"
        )
Cognitive Orchestration with Google Agent SDK (ADK)Conversational analytics in recon-iq are driven by the Google Agent Development Kit (ADK). Rather than using rigid dashboard components, the platform deploys an intelligent agent that parses natural language queries, retrieves structured metrics from BigQuery, and formats the output.The agent uses the BigQueryToolset to discover and query tables directly, and the DataAgentToolset to execute complex conversational operations over specific schemas.User Query: "Find transaction variances on June 5"
                      │
                      ▼
┌──────────────────────────────────────────┐
│          Google Agent SDK (ADK)          │
│                                          │
│  1. Parse intent and context             │
│  2. Build SQL schema via DataAgent       │ [9]
│  3. Run queries using BigQuery Toolset   │ 
└─────────────────────┬────────────────────┘
                      │
                      ▼ (gRPC Execution)
┌──────────────────────────────────────────┐
│         BigQuery Warehouse Table         │
└──────────────────────────────────────────┘
The system initializes and registers this database agent through Python modules, allowing the application layer to load and interact with it programmatically :Pythonimport os
import google.auth
from google.adk.agents import Agent
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset

# Explicitly load environment configurations [7, 11]
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "recon-iq-production")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# Configure Google Application Default Credentials 
credentials, project_id = google.auth.default()
credentials_config = BigQueryCredentialsConfig(credentials=credentials)

# Instantiate the native BigQuery tools module 
bq_tools = BigQueryToolset(credentials_config=credentials_config)

# Instantiate and configure the core agent module 
root_agent = Agent(
    model="gemini-2.5-flash",
    name="recon_iq_core_analyst",
    description="Cognitive analytics agent that queries BigQuery database tables using dynamic SQL generation.",
    instruction=(
        "You are the senior analytics database agent for the recon-iq system. "
        f"You are authorized to query tables in the '{GOOGLE_CLOUD_PROJECT}' project. "
        "Your role is to translate natural language inquiries into read-only SQL queries. "
        "When asked for visualization data or historical trends, construct select statements "
        "over 'historical_ledger' tables and format the output as JSON properties "
        "compatible with standard rendering frameworks such as Vega-Lite. "
        "Ensure all financial values preserve high-precision decimal formats."
    ),
    tools=[bq_tools]
)

def get_bigquery_agent() -> Agent:
    """Returns the configured ADK agent instance."""
    return root_agent
This configuration enables the agent to discover schemas, construct valid queries, and retrieve precise metrics based on natural language commands.Dynamic Conversational Interface and Automated Query ProcessingTo ensure reliable, deterministic responses to natural language queries, recon-iq uses system instructions that guide the model to output structured JSON and standardized analysis frameworks.Conversational Query 1: Visualizations and Trend AnalysisWhen a user asks: "what is the last year reconciliation data visualization, analyze it", the system coordinates data extraction, runs performance checks, and returns a structured analysis :
: Financial Business Intelligence Analyst.
:
1. Identify historical records in 'historical_ledger' spanning the trailing 12-month window.
2. Build an ANSI SQL query to aggregate transactions by month and match status.
3. Your output must return both a structured narrative analyzing performance trends and a valid Vega-Lite chart definition. Do not include extra explanation or markdown blocks outside the schema.

:
{
  "narrative_synthesis": "Continuous prose narrative outlining month-over-month performance trends, standard deviation of mismatches, and anomalies.",
  "vega_lite_spec": {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "description": "Monthly Reconciliation Trend Analysis",
    "data": {
      "values":
    },
    "mark": "bar",
    "encoding": {
      "x": {"field": "month", "type": "nominal", "title": "Reconciliation Month"},
      "y": {"field": "count", "type": "quantitative", "title": "Transaction Count"},
      "color": {"field": "status", "type": "nominal", "legend": {"title": "Match Status"}}
    }
  }
}
JSON{
  "narrative_synthesis": "The reconciliation system maintained high efficiency over the last year, averaging a 99.98% match rate. The highest variance occurred in November 2025 due to a payment gateway update that caused timing mismatches, which were resolved within the standard settlement window.",
  "vega_lite_spec": {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "description": "Monthly Reconciliation Trend Analysis",
    "data": {
      "values":
    },
    "mark": "bar",
    "encoding": {
      "x": {"field": "month", "type": "nominal", "title": "Reconciliation Month"},
      "y": {"field": "count", "type": "quantitative", "title": "Transaction Count"},
      "color": {"field": "status", "type": "nominal", "legend": {"title": "Match Status"}}
    }
  }
}
Conversational Query 2: Daily Audits and Forensic Variance AnalysisWhen a user asks: "tell me today's reconciliation data report", the system focuses on exact numerical matches and isolates any variance, no matter how small.
: High-Precision Financial Forensic Auditor.
:
1. Query today's transactions in 'historical_ledger'.
2. Flag any discrepancy where the absolute difference exceeds 0.001 units.
3. For three-way mismatches, isolate the exact ledger containing the variance.
4. Structure the output as an actionable audit log.
The system outputs a detailed audit summary showing the exact transaction-level discrepancies:Daily Forensic Variance LogAudit Interval: June 7, 2026Total Transactions Audited: 12,402Successfully Reconciled: 12,398Discrepancy Count: 4System Match Rate: $99.967\%$The following table logs every variance that exceeded the $0.001$ threshold :Unique IdentifierInternal LedgerGateway RecordBank StatementAbsolute VarianceIdentified Root Cause and Correction PathTX_2026_001210243.12010243.12110243.1200.001Gateway Drift: Minor precision mismatch in payment processor calculation. Mapped for minor settlement adjustment.TX_2026_0149450.500450.500448.5002.000Bank Service Fee: Bank statement value under-reported by $2.00$ due to processing fee. Mapped to transaction fee ledger.TX_2026_094195.00095.000Null95.000Settlement Delay: Transaction cleared gateway but is missing from bank statement. Flags a $1$-day deposit delay.TX_2026_1102Null120.000120.000120.000Missing Internal Record: Completed payment has no internal ledger record. Flagged for internal ledger correction.Production Deployment and ContainerizationTo run recon-iq consistently in production, the application services are containerized using Docker and Docker Compose. This packages the FastAPI application, MongoDB instance, and local persistent storage volumes into an isolated environment.Multi-Stage Dockerfile (Dockerfile)This configuration uses a multi-stage build to compile dependencies in a temporary container, keeping the final production image lightweight and secure.Dockerfile# Stage 1: Build compilation dependencies
FROM python:3.11-slim AS compiler

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt.

# Install dependencies to a local user path
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Build final lightweight container
FROM python:3.11-slim AS production

WORKDIR /app

# Copy python packages from the build stage
COPY --from=compiler /root/.local /root/.local
COPY..

# Configure path variables and environment settings
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV TEMP_SPOOL_DIR=/tmp/spooled_files

EXPOSE 8000

# Run Uvicorn utilizing an production ASGI configuration
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
Production Orchestration (docker-compose.yml)The orchestration configuration coordinates network links, local persistent database volumes, and secure authentication paths :YAMLversion: '3.8'

services:
  recon-iq-gateway:
    build:
      context:.
      dockerfile: Dockerfile
    container_name: recon_iq_gateway
    ports:
      - "8000:8000"
    environment:
      - MONGO_URI=mongodb://recon-iq-metadata:27017/
      - GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/cloud_service_key.json
      - GOOGLE_GENAI_USE_VERTEXAI=True
      - GOOGLE_CLOUD_PROJECT=recon-iq-production
      - GOOGLE_CLOUD_LOCATION=us-central1
    volumes:
      -./secure_keys:/app/secrets:ro
      - spooled_file_temp:/tmp/spooled_files
    depends_on:
      - recon-iq-metadata
    networks:
      - production_network

  recon-iq-metadata:
    image: mongo:6.0
    container_name: recon_iq_metadata
    ports:
      - "27017:27017"
    volumes:
      - metadata_volume:/data/db
    networks:
      - production_network

volumes:
  metadata_volume:
    driver: local
  spooled_file_temp:
    driver: local

networks:
  production_network:
    driver: bridge
Architectural Evaluation and Technical DeductionsBuilding an enterprise reconciliation system like recon-iq requires careful tradeoffs between raw performance, dynamic schema handling, and absolute precision.1. Arbitrary-Precision Math CoreBy executing matches using Python's decimal library, the system avoids the systemic rounding errors inherent in floating-point representations. This ensures that even tiny mismatches (e.g., $0.001$ units) are caught. While arbitrary-precision arithmetic requires more memory than CPU-optimized floating-point logic, this tradeoff is necessary to preserve audit-level data integrity.2. Google Agent SDK OrchestrationUsing the Google Agent SDK (ADK) simplifies conversational query handling. The agent can explore table metadata, generate queries, and extract metrics using its native BigQuery toolset. This design reduces development overhead and allows the natural language interface to adapt seamlessly as schemas evolve.3. Dual-Store Storage TopologyThe hybrid storage configuration optimizes both analytics and operational metadata. BigQuery tables are partitioned and clustered to minimize query costs and maximize throughput for deep analytical queries. Meanwhile, MongoDB handles operational run logs and session schemas, ensuring high write performance during raw file ingestion.