# MCP Security: Threat Modeling and Tool Poisoning Attacks

This repository contains the **complete threat modeling artifacts, experimental setup, and malicious MCP server implementations** used in the paper:

> **Model Context Protocol Threat Modeling and Analysis of Vulnerabilities to Prompt Injection with Tool Poisoning**  
> Charoes Huang, Xin Huang, Ngoc Phu Tran, Amin Milani Fard  
> *Journal of Cybersecurity and Privacy*, 6(3), 84, 2026  
> https://doi.org/10.3390/jcp6030084

The goal of this repository is to support reproducibility, and further research on the security of Model Context Protocol (MCP)–based AI agents, with a particular focus on client-side vulnerabilities to prompt injection via tool poisoning.

---

## 📄 Paper Overview

The Model Context Protocol (MCP) has rapidly emerged as a standard for connecting AI assistants to external tools and services. While MCP simplifies integration, it introduces new security risks that are poorly understood, particularly on the client side, where MCP clients implicitly trust server-provided tool metadata.

In our paper, we:

- Conduct comprehensive threat modeling of the MCP ecosystem using STRIDE and DREAD
- Identify 57 threats across six MCP components
- Show that tool poisoning is the most severe and exploitable client-side vulnerability
- Empirically evaluate seven major MCP clients using a malicious MCP server
- Demonstrate real-world attacks including:
  - Sensitive file exfiltration
  - Persistent surveillance via poisoned tools
  - Phishing link creation
  - Remote script execution
- Propose defense-in-depth mitigation strategies for MCP clients

This repository contains all supporting artifacts referenced in the paper.

---

## 📂 Repository Structure

```text
mcp-security/
├── threatmodel/
│   ├── STRIDE/
│   ├── DREAD/
│   ├── diagrams/
│   └── README.md
│
├── tool-poisoning/
│   ├── tool-poisoning.py
│   ├── malicious_tools/
│   └── README.md
│
├── test-result/
│   ├── logs/
│   ├── screenshots/
│   ├── client-behavior-analysis.md
│   └── README.md
│
├── scripts/
│   └── utilities/
│
└── README.md
```

## 🧠 Threat Modeling Artifacts
The `threatmodel/` directory contains the complete STRIDE and DREAD threat models used in the paper:

Coverage of six MCP components:

1. MCP Host  
2. MCP Client  
3. Large Language Model (LLM)  
4. MCP Server  
5. External Data Stores (files, APIs, tools)  
6. Authorization Server 

A total of 57 distinct threats were identified with STRIDE classification and DREAD severity scores.

## 🧪 Tool Poisoning Attacks
The `tool-poisoning/` directory provides a fully functional malicious MCP server used for experimental evaluation.
Features

Implements indirect prompt injection via poisoned tool descriptions
Supports multiple attack templates:

Hidden file reads
Priority manipulation
User activity logging
Phishing link generation
Remote code execution triggers

Compatible with standard MCP clients for reproducibility

⚠️ Warning: This code is intentionally malicious and must only be used in controlled, isolated environments for testing and research purposes.


## 📊 Experimental Results
The `test-result/` directory contains empirical evidence supporting the paper’s findings:

Attack success/failure matrices
Client-specific behavioral observations
Screenshots of UI prompts and approval dialogs
Tool invocation logs and parameter captures

🔬 Reproducibility
To reproduce the experiments:

Deploy the malicious MCP server in tool-poisoning/
Configure an MCP client to connect to the server
Issue benign user prompts (e.g., “add two numbers”)
Observe tool selection, parameter injection, and execution behavior
Compare results with the provided test documentation

⚠️ Experiments must not be conducted on production systems.

This repository is provided for defensive security research only.

## 📎 Citation
If you use this repository in academic or industrial research, please cite:

```APA
Huang, C., Huang, X., Tran, N. P., & Milani Fard, A. (2026). Model Context Protocol Threat Modeling and Analysis of Vulnerabilities to Prompt Injection with Tool Poisoning. Journal of Cybersecurity and Privacy, 6(3), 84. https://doi.org/10.3390/jcp6030084
```

```BibTeX
@Article{MCPSecurity_jcp6030084,
  AUTHOR = {Huang, Charoes and Huang, Xin and Tran, Ngoc Phu and Milani Fard, Amin},
  TITLE = {Model Context Protocol Threat Modeling and Analysis of Vulnerabilities to Prompt Injection with Tool Poisoning},
  JOURNAL = {Journal of Cybersecurity and Privacy},
  VOLUME = {6},
  YEAR = {2026},
  NUMBER = {3},
  ARTICLE-NUMBER = {84},
  URL = {https://www.mdpi.com/2624-800X/6/3/84},
  ISSN = {2624-800X},
  DOI = {10.3390/jcp6030084}
}
```

## 📄 License
This repository follows the same license as the paper:
Creative Commons Attribution (CC BY 4.0)
You are free to share and adapt this work with appropriate attribution.
