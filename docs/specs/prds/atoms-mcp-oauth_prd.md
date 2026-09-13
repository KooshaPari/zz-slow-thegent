# Product Requirements Document: atoms-mcp-oauth

**Version:** 1.0.0  
**Created:** 2026-02-18

## 1. Overview

# Atoms MCP OAuth 2.1 Server

## 2. Objectives

## 3. Success Metrics

## 4. Stakeholders

## 5. Target Users

## 6. Functional Requirements

### FR-1: OAuth 2.1 Compliance

Implements the latest OAuth 2.1 security standards with mandatory PKCE

### FR-2: Zero Environment Variables

All credentials stored securely in OS keychains

### FR-3: Multi-Tenant OAuth

Supports GitHub, Jira, Slack, and other provider integrations

### FR-4: Cross-Platform

Works on macOS, Windows, and Linux with native credential storage

### FR-5: SOC2 Ready

Comprehensive audit logging and security controls

### FR-6: Dual Transport

Supports both HTTP/SSE and stdio transports

### FR-7: Document Management

- `upload_document` - Upload files to projects

### FR-8: AI & Analysis

- `chat_with_ai` - AI-powered conversations

### FR-9: Project Management

- `list_projects` - View your projects

### FR-10: PKCE Required

All OAuth flows use S256 code challenge

### FR-11: Token Binding

Tokens bound to specific MCP instances

### FR-12: Automatic Expiry

Access tokens expire after 1 hour

### FR-13: Rotation on Use

Refresh tokens rotate on every use

### FR-14: Audit Logging

All operations logged with metadata

### FR-15: 1. First-Time Setup

### FR-16: 2. Claude Desktop Configuration

### FR-17: 3. Available Tools

### FR-18: Security Model

### FR-19: OAuth 2.1 Flow

### FR-20: Prerequisites

### FR-21: Building from Source

### FR-22: Running Tests

### FR-23: OAuth Providers

### FR-24: Advanced Settings

### FR-25: Common Issues

### FR-26: Debug Mode

### FR-27: Reporting Security Issues

### FR-28: Security Features

### FR-29: Development Workflow

### FR-30: No Stored Secrets

Uses public OAuth clients with PKCE

### FR-31: Token Rotation

Automatic refresh token rotation

### FR-32: Secure Storage

OS-native credential managers

### FR-33: Audit Trail

Every action logged for compliance

### FR-34: "Authentication failed"

- Ensure you have access to the Atoms platform

### FR-35: "Token storage failed"

- macOS: Grant keychain access when prompted

### FR-36: "OAuth callback timeout"

- Check firewall allows localhost:8080

## 7. Non-Functional Requirements

## 8. Features

### 🟡 OAuth 2.1 Compliance

Implements the latest OAuth 2.1 security standards with mandatory PKCE

### 🟡 Zero Environment Variables

All credentials stored securely in OS keychains

### 🟡 Multi-Tenant OAuth

Supports GitHub, Jira, Slack, and other provider integrations

### 🟡 Cross-Platform

Works on macOS, Windows, and Linux with native credential storage

### 🟡 SOC2 Ready

Comprehensive audit logging and security controls

### 🟡 Dual Transport

Supports both HTTP/SSE and stdio transports

### 🟡 Document Management

- `upload_document` - Upload files to projects

### 🟡 AI & Analysis

- `chat_with_ai` - AI-powered conversations

### 🟡 Project Management

- `list_projects` - View your projects

### 🟡 PKCE Required

All OAuth flows use S256 code challenge

### 🟡 Token Binding

Tokens bound to specific MCP instances

### 🟡 Automatic Expiry

Access tokens expire after 1 hour

### 🟡 Rotation on Use

Refresh tokens rotate on every use

### 🟡 Audit Logging

All operations logged with metadata

### 🟡 1. First-Time Setup

### 🟡 2. Claude Desktop Configuration

### 🟡 3. Available Tools

### 🟡 Security Model

### 🟡 OAuth 2.1 Flow

### 🟡 Prerequisites

### 🟡 Building from Source

### 🟡 Running Tests

### 🟡 OAuth Providers

### 🟡 Advanced Settings

### 🟡 Common Issues

### 🟡 Debug Mode

### 🟡 Reporting Security Issues

### 🟡 Security Features

### 🟡 Development Workflow

### 🟡 No Stored Secrets

Uses public OAuth clients with PKCE

### 🟡 Token Rotation

Automatic refresh token rotation

### 🟡 Secure Storage

OS-native credential managers

### 🟡 Audit Trail

Every action logged for compliance

### 🟡 "Authentication failed"

- Ensure you have access to the Atoms platform

### 🟡 "Token storage failed"

- macOS: Grant keychain access when prompted

### 🟡 "OAuth callback timeout"

- Check firewall allows localhost:8080

## 9. Architecture Overview

Architecture details to be documented.

## 10. Technical Requirements

- Use node.js

## 11. Integration Points

- **Integration with Management**: Integration point with Management project
- **Integration with with**: Integration point with with project
- **Integration with -**: Integration point with - project
- **Integration with access**: Integration point with access project

## 12. Timeline & Phases

## 13. Milestones

## 14. Dependencies

## 16. Related Projects

- Management
- with
- -
- access

## 17. Shared Features

- Common Issues
- Debug Mode
- Audit Trail
- Audit Logging
- Prerequisites
- Running Tests
- OAuth Flow
- Development Workflow
- 📱 Cross-platform
- Security Features
- Analysis:
- 3. Project Management
- Claude Desktop Configuration
- Document Management
- Building from Source
