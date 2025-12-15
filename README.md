# bl4ck0PS

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/blackglobeco/bl4ck0PS.git
   cd bl4ck0PS
   ```

2. Run the application:
   - Linux: `./start_blackai.sh`
   - Windows: `start_blackai.bat`

The startup script will automatically:
- Check for updates
- Set up the Python environment
- Install dependencies
- Launch bl4ck0PS

In order to use Email Lookup transform
You need to login with GHunt first.
After starting the pano via starter scripts;

1. Select venv manually
   - Linux: `source venv/bin/activate`
   - Windows: `call venv\Scripts\activate`
3. See how to login [here](https://github.com/mxrch/GHunt/?tab=readme-ov-file#login)

## 💡 Quick Start Guide

1. **Create Investigation**: Start a new investigation or load an existing one
2. **Add Entities**: Drag entities from the sidebar onto the graph
3. **Discover Connections**: Use transforms to automatically find relationships
4. **Analyze**: Use timeline and map views to understand patterns
5. **Save**: Export your investigation for later use

## 🔍 Features

### 🕸️ Core Functionality

- **Interactive Graph Visualization**
  - Drag-and-drop entity creation
  - Multiple layout algorithms (Circular, Hierarchical, Radial, Force-Directed)
  - Dynamic relationship mapping
  - Visual node and edge styling

- **Timeline Analysis**
  - Chronological event visualization
  - Interactive timeline navigation
  - Event filtering and grouping
  - Temporal relationship analysis

- **Map Integration**
  - Geographic data visualization
  - Location-based analysis
  - Interactive mapping features
  - Coordinate plotting and tracking

### 🎯 Entity Management

- **Supported Entity Types**
  - 📧 Email addresses
  - 👤 Usernames
  - 🌐 Websites
  - 🖼️ Images
  - 📍 Locations
  - ⏰ Events
  - 📝 Text content
  - 🔧 Custom entity types

### 🔄 Transform System

- **Email Analysis**
  - Google account investigation
  - Calendar event extraction
  - Location history analysis
  - Connected services discovery

- **Username Analysis**
  - Cross-platform username search
  - Social media profile discovery
  - Platform correlation
  - Web presence analysis

- **Image Analysis**
  - Reverse image search
  - Visual content analysis
  - Metadata extraction
  - Related image discovery

### 🤖 AI Integration

- **bl4ckAI**
  - Natural language investigation assistant
  - Automated entity extraction and relationship mapping
  - Pattern recognition and anomaly detection
  - Multi-language support
  - Context-aware suggestions
  - Timeline and graph analysis

## 🧩 Core Components

### 📦 Entities

Entities are the fundamental building blocks of PANO. They represent distinct pieces of information that can be connected and analyzed:

- **Built-in Types**
  - 📧 Email: Email addresses with service detection
  - 👤 Username: Social media and platform usernames
  - 🌐 Website: Web pages with metadata
  - 🖼️ Image: Images with EXIF and analysis
  - 📍 Location: Geographic coordinates and addresses
  - ⏰ Event: Time-based occurrences
  - 📝 Text: Generic text content

- **Properties System**
  - Type-safe property validation
  - Automatic property getters
  - Dynamic property updates
  - Custom property types
  - Metadata support

### ⚡ Transforms

Transforms are automated operations that process entities to discover new information and relationships:

- **Operation Types**
  - 🔍 Discovery: Find new entities from existing ones
  - 🔗 Correlation: Connect related entities
  - 📊 Analysis: Extract insights from entity data
  - 🌐 OSINT: Gather open-source intelligence
  - 🔄 Enrichment: Add data to existing entities

- **Features**
  - Async operation support
  - Progress tracking
  - Error handling
  - Rate limiting
  - Result validation

### 🛠️ Helpers

Helpers are specialized tools with dedicated UIs for specific investigation tasks:

- **Available Helpers**
  - 🔍 Cross-Examination: Analyze statements and testimonies
  - 👤 Portrait Creator: Generate facial composites
  - 📸 Media Analyzer: Advanced image processing and analysis
  - 🔍 Base Searcher: Search near places of interest
  - 🔄 Translator: Translate text between languages

- **Helper Features**
  - Custom Qt interfaces
  - Real-time updates
  - Graph integration
  - Data visualization
  - Export capabilities

