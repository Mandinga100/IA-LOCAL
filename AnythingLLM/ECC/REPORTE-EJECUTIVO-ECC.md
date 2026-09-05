# Reporte Ejecutivo — ECC (Everything Claude Code) v2.0.0

**Fecha del análisis:** 2026-07-08
**Repositorio:** `affaan-m/ECC` (https://github.com/affaan-m/ECC)
**Propósito:** Sistema operativo harness-native para agentes de IA
**Licencia:** MIT | **Autor:** Affaan Mustafa

---

## Índice

1. [Resumen General](#1-resumen-general)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Catálogo Completo de Agentes](#3-catálogo-completo-de-agentes)
4. [Catálogo de Comandos](#4-catálogo-de-comandos)
5. [Catálogo de Skills](#5-catálogo-de-skills)
6. [Sistema de Automatizaciones (Hooks)](#6-sistema-de-automatizaciones-hooks)
7. [Workflows](#7-workflows)
8. [Análisis Forense de Seguridad](#8-análisis-forense-de-seguridad)
9. [Resumen de Infraestructura](#9-resumen-de-infraestructura)
10. [Conclusiones](#10-conclusiones)

---

## 1. Resumen General

**ECC** es un ecosistema completo de productividad para desarrollo de software asistido por agentes de IA. Funciona como una capa operativa sobre múltiples asistentes de código (Claude Code, Codex, Cursor, OpenCode, Gemini, Zed, y otros) proporcionando:

| Dimensión | Cantidad |
|-----------|----------|
| Agentes especializados | **67** |
| Skills (flujos de trabajo) | **278** |
| Comandos | **93** |
| Scripts de automatización (hooks) | **49** |
| Workflows nativos | **1** |
| Rule packs por lenguaje | **22** |
| Archivos totales | **3,301** |
| Líneas de código | ~300,000+ |

### Componentes principales

| Componente | Descripción |
|------------|-------------|
| **Agentes** | Subagentes especializados para tareas concretas (revisión, planificación, seguridad, testing, etc.) |
| **Skills** | Flujos de trabajo reutilizables con instrucciones detalladas para el agente |
| **Comandos** | Atajos slash (/plan, /code-review, /test-coverage, etc.) |
| **Hooks** | Automatizaciones que se ejecutan en eventos del ciclo de vida del agente |
| **Rules** | Guías de estilo, seguridad y patrones para 22+ lenguajes |
| **Continuous Learning** | Sistema que aprende patrones de sesiones y los convierte en skills |
| **AgentShield** | Auditor de seguridad para configuraciones de agentes IA |
| **ECC Tools** | GitHub App de pago con análisis de PR y gobierno |

---

## 2. Arquitectura del Sistema

```
                    ┌─────────────────────────────────────┐
                    │         ECC TOOLS (GitHub App)       │
                    │   $19/seat - PR audits, governance   │
                    └─────────────────────────────────────┘
                                    │
                    ┌─────────────────────────────────────┐
                    │         ECC 2.0 CONTROL PLANE        │
                    │   (Rust TUI - sesiones, worktrees)   │
                    └─────────────────────────────────────┘
                                    │
    ┌───────────────┬───────────────┼───────────────┬───────────────┐
    │               │               │               │               │
    ▼               ▼               ▼               ▼               ▼
┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐
│ Claude │    │ Codex  │    │ Cursor │    │OpenCode│    │ Gemini │
│ Code   │    │        │    │        │    │        │    │        │
└────────┘    └────────┘    └────────┘    └────────┘    └────────┘
    │               │               │               │               │
    └───────────────┴───────────────┴───────────────┴───────────────┘
                                    │
                    ┌─────────────────────────────────────────────┐
                    │          ECC LAYER (este repositorio)        │
                    │                                              │
                    │  ┌──────┐ ┌──────┐ ┌──────┐ ┌───────────┐  │
                    │  │Agents│ │Skills│ │Hooks │ │  Rules    │  │
                    │  │  (67)│ │(278) │ │ (49) │ │(22 langs) │  │
                    │  └──────┘ └──────┘ └──────┘ └───────────┘  │
                    │  ┌──────┐ ┌──────┐ ┌──────────────────┐   │
                    │  │Cmds  │ │MCP   │ │Continuous        │   │
                    │  │ (93) │ │Config│ │Learning v2       │   │
                    │  └──────┘ └──────┘ └──────────────────┘   │
                    └─────────────────────────────────────────────┘
```

### Estructura de directorios

```
ECC/
├── agents/           → 67 subagentes especializados (.md)
├── .agents/          → Skills instalables con manifiestos OpenAI
├── skills/           → 278 flujos de trabajo reutilizables
├── commands/         → 93 comandos slash (/plan, /review, etc.)
├── hooks/            → Configuración de automatizaciones
├── scripts/hooks/    → 49 scripts ejecutables para hooks
├── rules/            → Guías para 22+ lenguajes de programación
├── ecc2/             → Control plane en Rust (TUI)
├── scripts/          → Utilidades CLI (instalación, auditoría, etc.)
├── tests/            → Suite de tests (997+ validaciones)
├── mcp-configs/      → Configuraciones de servidores MCP
├── workflows/        → Workflows nativos de Claude Code
├── docs/             → Documentación en 12 idiomas
├── src/llm/          → Capa de abstracción LLM en Python
└── config/           → Esquemas y configuraciones base
```

---

## 3. Catálogo Completo de Agentes

### 3.1 Agentes de Orquestación y Planificación (9)

| Agente | Función Principal | Modelo |
|--------|-------------------|--------|
| **architect** | Diseño de arquitectura de sistemas, escalabilidad, decisiones técnicas | Opus |
| **planner** | Planificación de features complejos, refactorización, identificación de riesgos | Opus |
| **code-reviewer** | Revisión de calidad, seguridad y mantenibilidad del código | Sonnet |
| **code-architect** | Diseño de arquitectura de features basado en patrones del codebase | Sonnet |
| **code-explorer** | Trazado de rutas de ejecución, mapeo de capas de arquitectura | Sonnet |
| **code-simplifier** | Simplificación y refinamiento de código para claridad y mantenibilidad | Sonnet |
| **refactor-cleaner** | Limpieza de código muerto, deduplicación, consolidación | Sonnet |
| **build-error-resolver** | Resolución de errores de build/TypeScript con diffs mínimos | Sonnet |
| **chief-of-staff** | Triage de comunicaciones (email, Slack, LINE, Messenger) en 4 niveles | Opus |

### 3.2 Agentes de Revisión por Lenguaje (17)

| Agente | Lenguaje | Enfoque |
|--------|----------|---------|
| **typescript-reviewer** | TypeScript/JavaScript | Type safety, async, Node/web security |
| **python-reviewer** | Python | PEP 8, type hints, patrones Pythonic |
| **java-reviewer** | Java/Spring Boot/Quarkus | JPA, arquitectura en capas, seguridad |
| **go-reviewer** | Go | Concurrencia, manejo de errores, idiomatic Go |
| **rust-reviewer** | Rust | Ownership, lifetimes, unsafe, idiomatic Rust |
| **cpp-reviewer** | C/C++ | Memoria segura, C++ moderno, concurrencia |
| **csharp-reviewer** | C#/.NET | Convenciones .NET, async, nullable reference types |
| **swift-reviewer** | Swift | Protocol-oriented design, value semantics, ARC |
| **kotlin-reviewer** | Kotlin/Android/KMP | Corrutinas, Compose, patrones Kotlin |
| **fsharp-reviewer** | F# | Functional idioms, type safety, computation expressions |
| **php-reviewer** | PHP | PSR-12, PHP type system, Eloquent |
| **django-reviewer** | Python/Django | ORM, DRF, migraciones seguras |
| **fastapi-reviewer** | Python/FastAPI | Async, DI, Pydantic, OpenAPI |
| **react-reviewer** | JavaScript/React | Hooks, render performance, server/client components |
| **vue-reviewer** | JavaScript/Vue | Composition API, reactividad, seguridad en templates |
| **flutter-reviewer** | Dart/Flutter | Widgets, state management, rendimiento |
| **harmonyos-app-resolver** | ArkTS/ArkUI | HarmonyOS, V2 state management |

### 3.3 Agentes de Resolución de Build (10)

| Agente | Resuelve errores de |
|--------|---------------------|
| **java-build-resolver** | Java/Maven/Gradle/Spring Boot/Quarkus |
| **kotlin-build-resolver** | Kotlin/Gradle/compilador/dependencias |
| **cpp-build-resolver** | C++/CMake/linker/templates |
| **rust-build-resolver** | Cargo/borrow checker/dependencias |
| **go-build-resolver** | Go build/vet/linter |
| **swift-build-resolver** | Swift/Xcode/SPM/code-signing |
| **dart-build-resolver** | Dart/Flutter analyze/pub/build_runner |
| **react-build-resolver** | Vite/webpack/Next.js/CRA/hidratación JSX |
| **django-build-resolver** | Pip/Poetry/migraciones/collectstatic |
| **pytorch-build-resolver** | Tensores/CUDA/gradientes/DataLoader |

### 3.4 Agentes de Testing y TDD (4)

| Agente | Descripción |
|--------|-------------|
| **tdd-guide** | Metodología test-first, cobertura 80%+, ciclo RED-GREEN-IMPROVE |
| **e2e-runner** | Tests end-to-end con Vercel Agent Browser + Playwright |
| **pr-test-analyzer** | Análisis de calidad y completitud de tests en PRs |
| **agent-evaluator** | Evaluación con rúbrica de calidad en 5 ejes |

### 3.5 Agentes de Seguridad (4)

| Agente | Descripción |
|--------|-------------|
| **security-reviewer** | OWASP Top 10, SSRF, inyección, detección de secretos |
| **healthcare-reviewer** | Seguridad clínica, cumplimiento PHI, precisión CDSS |
| **silent-failure-hunter** | Detección de errores silenciados, fallbacks incorrectos |
| **opensource-sanitizer** | Escaneo de secretos/PII filtrados antes de releases |

### 3.6 Agentes de Dominios Especializados (13)

| Agente | Especialidad |
|--------|-------------|
| **database-reviewer** | PostgreSQL/Supabase: optimización de queries, esquemas, seguridad |
| **mle-reviewer** | ML pipelines, feature stores, model serving/monitoreo |
| **performance-optimizer** | Análisis de bottlenecks, tamaño de bundle, memoria, algoritmos |
| **seo-specialist** | SEO técnico, datos estructurados, Core Web Vitals |
| **a11y-architect** | Cumplimiento WCAG 2.2, principios POUR |
| **docs-lookup** | Consulta de documentación de librerías via Context7 MCP |
| **doc-updater** | Mantenimiento de codemaps, READMEs, documentación |
| **marketing-agent** | Planificación de campañas, copy, investigación de audiencia |
| **conversation-analyzer** | Análisis de transcripciones para patrones merecedores de hooks |
| **comment-analyzer** | Precisión de comentarios, riesgo de rot, completitud |
| **type-design-analyzer** | Encapsulación, expresión de invariantes, utilidad de tipos |
| **spec-miner** | Extracción de especificaciones de comportamiento de codebases existentes |
| **homelab-architect** | Planes de red doméstica, cambios por etapas, rollback |

### 3.7 Agentes de Redes (3)

| Agente | Descripción |
|--------|-------------|
| **network-architect** | Arquitectura de red empresarial/multi-sitio |
| **network-config-reviewer** | Seguridad y corrección de configuraciones de router/switch |
| **network-troubleshooter** | Diagnóstico de conectividad por capas OSI |

### 3.8 Agentes de Infraestructura (5)

| Agente | Descripción |
|--------|-------------|
| **harness-optimizer** | Optimización de configuración de agent harness: confiabilidad, costo, rendimiento |
| **loop-operator** | Operación de loops autónomos, monitoreo, intervención |
| **gan-planner** | Planificador GAN Harness: especificación desde prompt de una línea |
| **gan-generator** | Generador GAN Harness: implementación e iteración |
| **gan-evaluator** | Evaluador GAN Harness: tests Playwright vs rúbrica |

### 3.9 Agentes de Open Source Pipeline (3)

| Agente | Descripción |
|--------|-------------|
| **opensource-forker** | Fork y sanitización de secretos, generación de .env.example |
| **opensource-sanitizer** | Verificación de sanitización antes de release |
| **opensource-packager** | Generación de CLAUDE.md, README, LICENSE, templates |

---

## 4. Catálogo de Comandos

Los comandos son accesos directos slash (/) que invocan agentes o flujos de trabajo específicos.

### 4.1 Comandos de Planificación y Gestión

| Comando | Función |
|---------|---------|
| `/plan` | Planificación de implementación de features |
| `/plan-prd` | Generación de PRD (Product Requirements Document) |
| `/epic-claim` | Asignación de épica |
| `/epic-decompose` | Descomposición de épica en tareas |
| `/epic-publish` | Publicación de épica |
| `/epic-review` | Revisión de épica |
| `/epic-sync` | Sincronización de épica |
| `/epic-unblock` | Desbloqueo de épica |
| `/epic-validate` | Validación de épica |
| `/project-init` | Inicialización de proyecto |
| `/projects` | Gestión de proyectos |
| `/feature-dev` | Desarrollo de features |

### 4.2 Comandos de Revisión y Calidad

| Comando | Función |
|---------|---------|
| `/code-review` | Revisión de calidad de código |
| `/review-pr` | Revisión de Pull Request |
| `/pr` | Gestión de PRs |
| `/quality-gate` | Gate de verificación de calidad |
| `/test-coverage` | Análisis de cobertura de tests |
| `/security-scan` | Escaneo de seguridad con AgentShield |

### 4.3 Comandos de Build y Lenguajes

| Comando | Función |
|---------|---------|
| `/build-fix` | Corrección de errores de build |
| `/cpp-build` | Build C++ |
| `/cpp-review` | Revisión de código C++ |
| `/cpp-test` | Testing C++ |
| `/flutter-build` | Build Flutter |
| `/flutter-review` | Revisión Flutter |
| `/flutter-test` | Testing Flutter |
| `/go-build` | Build Go |
| `/go-review` | Revisión Go |
| `/go-test` | Testing Go |
| `/gradle-build` | Build Gradle |
| `/kotlin-build` | Build Kotlin |
| `/kotlin-review` | Revisión Kotlin |
| `/kotlin-test` | Testing Kotlin |
| `/python-review` | Revisión Python |
| `/react-build` | Build React |
| `/react-review` | Revisión React |
| `/react-test` | Testing React |
| `/rust-build` | Build Rust |
| `/rust-review` | Revisión Rust |
| `/rust-test` | Testing Rust |
| `/vue-review` | Revisión Vue |
| `/fastapi-review` | Revisión FastAPI |

### 4.4 Comandos de Aprendizaje Continuo

| Comando | Función |
|---------|---------|
| `/learn` | Extracción de patrones en medio de sesión |
| `/learn-eval` | Extracción, evaluación y guardado de patrones |
| `/evolve` | Agrupación de instintos en skills |
| `/instinct-status` | Visualización de instintos aprendidos |
| `/instinct-import` | Importación de instintos |
| `/instinct-export` | Exportación de instintos |
| `/prune` | Eliminación de instintos pendientes expirados |

### 4.5 Comandos de Automatización y Loops

| Comando | Función |
|---------|---------|
| `/loop-start` | Inicio de loop autónomo |
| `/loop-status` | Estado de loop autónomo |
| `/santa-loop` | Loop estilo Santa (verificación continua) |
| `/multi-plan` | Descomposición multi-agente de tareas |
| `/multi-execute` | Workflows multi-agente orquestados |
| `/multi-backend` | Orquestación multi-servicio backend |
| `/multi-frontend` | Orquestación multi-servicio frontend |
| `/multi-workflow` | Workflows multi-servicio generales |
| `/pm2` | Gestión de ciclo de vida de servicios PM2 |
| `/auto-update` | Actualización automática de ECC |

### 4.6 Comandos de Hooks y Configuración

| Comando | Función |
|---------|---------|
| `/hookify` | Creación conversacional de hooks |
| `/hookify-configure` | Configuración de hookify |
| `/hookify-help` | Ayuda de hookify |
| `/hookify-list` | Listado de hooks disponibles |
| `/setup-pm` | Configuración de package manager |
| `/model-route` | Enrutamiento de modelo |
| `/harness-audit` | Auditoría de harness |

### 4.7 Comandos de Sesión y Documentación

| Comando | Función |
|---------|---------|
| `/sessions` | Gestión de historial de sesiones |
| `/save-session` | Guardado de sesión actual |
| `/resume-session` | Reanudación de sesión |
| `/checkpoint` | Guardado de estado de verificación |
| `/update-docs` | Actualización de documentación |
| `/update-codemaps` | Actualización de codemaps |
| `/skill-create` | Generación de skills desde historial git |
| `/skill-health` | Estado de salud de skills |
| `/cost-report` | Reporte de costos |

### 4.8 Comandos de Marketing y ORCH

| Comando | Función |
|---------|---------|
| `/marketing-campaign` | Campaña de marketing |
| `/promote` | Promoción |
| `/orch-add-feature` | ORCH: añadir feature |
| `/orch-build-mvp` | ORCH: construir MVP |
| `/orch-change-feature` | ORCH: cambiar feature |
| `/orch-fix-defect` | ORCH: corregir defecto |
| `/orch-refine-code` | ORCH: refinar código |
| `/orch-review` | ORCH: revisar |
| `/jira` | Integración con Jira |
| `/aside` | Comando auxiliar |

---

## 5. Catálogo de Skills

Los skills son flujos de trabajo reutilizables y domain knowledge que el agente puede invocar. A diferencia de los comandos (atajos), los skills contienen instrucciones detalladas paso a paso.

### 5.1 Skills de Lenguajes y Frameworks

| Categoría | Skills incluidos |
|-----------|-----------------|
| **Python** | python-patterns, python-testing, fastapi-patterns, django-patterns, django-security, django-tdd, django-verification, django-celery, pytorch-patterns |
| **TypeScript/JavaScript** | react-patterns, react-testing, react-performance, react-native-patterns, vue-patterns, angular-developer, nextjs-turbopack, nuxt4-patterns, nodejs-keccak256, vite-patterns |
| **Java** | springboot-patterns, springboot-security, springboot-tdd, springboot-verification, quarkus-patterns, quarkus-security, quarkus-tdd, quarkus-verification, jpa-patterns, java-coding-standards |
| **Go** | golang-patterns, golang-testing |
| **Rust** | rust-patterns, rust-testing |
| **Kotlin** | kotlin-patterns, kotlin-testing, kotlin-coroutines-flows, kotlin-exposed-patterns, kotlin-ktor-patterns, compose-multiplatform-patterns |
| **Swift** | swiftui-patterns, swift-actor-persistence, swift-concurrency-6-2, swift-protocol-di-testing |
| **PHP** | laravel-patterns, laravel-security, laravel-tdd, laravel-verification, laravel-plugin-discovery, php-patterns, php-security, php-testing |
| **C/C++** | cpp-coding-standards, cpp-testing |
| **C#/.NET** | dotnet-patterns, csharp-testing |
| **Dart/Flutter** | dart-flutter-patterns, flutter-dart-code-review |
| **Perl** | perl-patterns, perl-security, perl-testing |
| **F#** | fsharp-testing |
| **HarmonyOS** | (incluido en harmonyos-app-resolver agent) |

### 5.2 Skills de Infraestructura y DevOps

| Skill | Descripción |
|-------|-------------|
| docker-patterns | Docker Compose, networking, volúmenes, seguridad |
| kubernetes-patterns | Orquestación K8s, deployments, servicios |
| deployment-patterns | CI/CD, health checks, rollbacks |
| database-migrations | Patrones de migración (Prisma, Drizzle, Django, Go) |
| postgres-patterns | Optimización PostgreSQL, indexing, queries |
| mysql-patterns | Patrones MySQL |
| redis-patterns | Patrones Redis, caching, sesiones |
| prisma-patterns | Patrones Prisma ORM |
| terraform-patterns | Infraestructura como código |
| github-ops | Automatización de GitHub |
| terminal-ops | Operaciones de terminal |
| homelab-network-setup | Configuración de red doméstica |
| homelab-vlan-segmentation | Segmentación VLAN |
| homelab-wireguard-vpn | VPN WireGuard |
| homelab-pihole-dns | DNS con PiHole |
| homelab-network-readiness | Preparación de red homelab |

### 5.3 Skills de Seguridad

| Skill | Descripción |
|-------|-------------|
| security-review | Checklist OWASP Top 10, detección de secretos |
| security-scan | Integración con AgentShield |
| security-bounty-hunter | Caza de vulnerabilidades |
| healthcare-phi-compliance | Cumplimiento PHI (HIPAA) |
| hipaa-compliance | Cumplimiento HIPAA completo |
| defi-amm-security | Seguridad DeFi/AMM |
| llm-trading-agent-security | Seguridad de agentes de trading LLM |
| opensource-pipeline | Pipeline de open source sanitizado |

### 5.4 Skills de Testing y Calidad

| Skill | Descripción |
|-------|-------------|
| tdd-workflow | Flujo TDD completo (RED-GREEN-IMPROVE) |
| verification-loop | Loop de verificación continua |
| eval-harness | Harness de evaluación con gradedores |
| e2e-testing | Tests E2E con Playwright |
| ai-regression-testing | Testing de regresión para AI |
| benchmark-methodology | Metodología de benchmarks |
| benchmark-optimization-loop | Loop de optimización de benchmarks |
| plankton-code-quality | Calidad de código en tiempo de escritura |
| codehealth-mcp | CodeScene Code Health MCP |

### 5.5 Skills de Aprendizaje Continuo

| Skill | Descripción |
|-------|-------------|
| continuous-learning | v1: Extracción de patrones via Stop-hook |
| continuous-learning-v2 | v2: Sistema basado en instintos con scoring de confianza |
| instinct-cli | CLI de gestión de instintos |
| iterative-retrieval | Refinamiento progresivo de contexto para subagentes |
| strategic-compact | Sugerencias de compactación manual |
| skill-scout | Descubrimiento de skills |
| skill-stocktake | Auditoría de calidad de skills y comandos |

### 5.6 Skills de Dominios de Negocio

| Skill | Descripción |
|-------|-------------|
| article-writing | Escritura de artículos largos con voz definida |
| content-engine | Contenido multi-plataforma y repurposing |
| market-research | Investigación de mercado con atribución de fuentes |
| investor-materials | Pitch decks, one-pagers, memos, modelos financieros |
| investor-outreach | Outreach personalizado para fundraising |
| brand-discovery | Descubrimiento de marca |
| brand-voice | Voz de marca consistente |
| seo | SEO técnico |
| social-publisher | Publicación en redes sociales |
| social-graph-ranker | Ranking de grafo social |
| email-ops | Operaciones de email |
| messages-ops | Operaciones de mensajería |
| unified-notifications-ops | Notificaciones unificadas |
| customer-billing-ops | Operaciones de facturación |
| finance-billing-ops | Operaciones financieras |
| lead-intelligence | Inteligencia de leads |
| carrier-relationship-management | Gestión de relaciones con carriers |
| logistics-exception-management | Gestión de excepciones logísticas |
| returns-reverse-logistics | Logística inversa |
| inventory-demand-planning | Planificación de demanda de inventario |
| production-scheduling | Programación de producción |
| quality-nonconformance | No conformidades de calidad |
| energy-procurement | Abastecimiento de energía |
| customs-trade-compliance | Cumplimiento aduanero |
| visa-doc-translate | Traducción de documentos de visa |

### 5.7 Skills de Media y Contenido

| Skill | Descripción |
|-------|-------------|
| frontend-slides | Presentaciones HTML sin dependencias |
| manim-video | Creación de videos con Manim |
| remotion-video-creation | Creación de videos con Remotion |
| video-editing | Edición de video |
| videodb | Ingesta, búsqueda, edición, generación y streaming de video/audio |
| fal-ai-media | Generación de media con Fal.ai |
| x-api | API de X (Twitter) |
| crosspost | Cross-posting multi-plataforma |
| ui-demo | Demos de UI |
| ui-to-vue | Conversión de UI a Vue |

### 5.8 Skills de MCP y Herramientas

| Skill | Descripción |
|-------|-------------|
| mcp-server-patterns | Patrones para servidores MCP |
| exa-search | Búsqueda con Exa |
| search-first | Flujo de investigación antes de codificar |
| documentation-lookup | Consulta de documentación via Context7 |
| nutrient-document-processing | Procesamiento de documentos con Nutrient API |
| nanoclaw-repl | REPL de NanoClaw |
| hookify-rules | Hookification de reglas |

### 5.9 Skills de ORCH (Orquestación)

| Skill | Descripción |
|-------|-------------|
| orch-add-feature | Añadir feature con orquestación |
| orch-build-mvp | Construir MVP orquestado |
| orch-change-feature | Cambiar feature orquestado |
| orch-fix-defect | Corregir defecto orquestado |
| orch-pipeline | Pipeline de orquestación |
| orch-refine-code | Refinar código orquestado |

### 5.10 Skills de Machine Learning

| Skill | Descripción |
|-------|-------------|
| mle-workflow | ML pipelines, data contracts, evals, deployment, monitoring |
| pytorch-patterns | Patrones de deep learning con PyTorch |
| ml-adoption-playbook | Playbook de adopción de ML |
| recsys-pipeline-architect | Arquitectura de pipelines de recomendación |
| foundation-models-on-device | Modelos fundacionales en dispositivo |
| prediction-market-oracle-research | Investigación de oráculos para mercados de predicción |
| prediction-market-risk-review | Revisión de riesgos de mercados de predicción |
| ito-market-intelligence | Inteligencia de mercado Itô |
| ito-basket-compare | Comparación de baskets Itô |
| ito-trade-planner | Planificador de trades Itô |
| ito-data-atlas-agent | Agente de atlas de datos Itô |

---

## 6. Sistema de Automatizaciones (Hooks)

El sistema de hooks permite automatizar acciones en puntos específicos del ciclo de vida del agente.

### 6.1 Puntos de Hook

| Punto | Momento de ejecución |
|-------|---------------------|
| **PreToolUse** | Antes de ejecutar una herramienta (Bash, Write, Edit, etc.) |
| **PostToolUse** | Después de ejecutar una herramienta |
| **SessionStart** | Al inicio de una sesión |
| **SessionEnd** | Al finalizar una sesión |
| **PreCompact** | Antes de una compactación de contexto |
| **Stop** | Cuando se detiene la ejecución |
| **PostToolUseFailure** | Cuando falla una herramienta |

### 6.2 Hooks Implementados

#### PreToolUse (11 hooks)

| Hook | Disparador | Función |
|------|------------|---------|
| **pre:bash:dispatcher** | Bash | Preflight de Bash: calidad, tmux, push, GateGuard |
| **pre:write:doc-file-warning** | Write | Advertencia sobre archivos doc no estándar |
| **pre:edit-write:suggest-compact** | Edit/Write | Sugerencia de compactación manual |
| **pre:observe:continuous-learning** | Cualquier | Captura de uso de herramientas para aprendizaje |
| **pre:governance-capture** | Bash/Write/Edit/MultiEdit | Captura de eventos de gobernanza |
| **pre:config-protection** | Write/Edit/MultiEdit | Bloqueo de cambios a config de linter/formatter |
| **pre:mcp-health-check** | Cualquiera | Verificación de salud de MCP |
| **pre:edit-write:gateguard-fact-force** | Edit/Write/MultiEdit | Bloqueo de primera edición por archivo (investigación forzada) |
| **pre:observe-runner** | Cualquiera | Runner de observación para aprendizaje |
| **pre:bash-dev-server-block** | Bash | Bloqueo de dev server en producción |
| **pre:bash-git-push-reminder** | Bash | Recordatorio de git push |
| **pre:bash-commit-quality** | Bash | Verificación de calidad de commit |
| **pre:bash-tmux-reminder** | Bash | Recordatorio de tmux |
| **pre:write-doc-warn** | Write | Advertencia de documentación |
| **pretooluse-visible-output** | Cualquiera | Output visible de pre-tool |
| **config-protection** | Write/Edit | Protección de configuración |
| **gateguard-fact-force** | Edit/Write | GateGuard |
| **block-no-verify** | Cualquiera | Bloqueo sin verificación |

#### PostToolUse (10 hooks)

| Hook | Disparador | Función |
|------|------------|---------|
| **post:bash:dispatcher** | Bash | Postflight: logging, PR, build notify |
| **post:quality-gate** | Edit/Write/MultiEdit | Gate de calidad después de ediciones |
| **post:edit:design-quality-check** | Edit/Write/MultiEdit | Advertencia sobre UI template genérica |
| **post:edit:accumulator** | Edit/Write/MultiEdit | Registro de archivos JS/TS editados para batch format |
| **post:edit:console-warn** | Edit | Advertencia sobre console.log |
| **post:governance-capture** | Bash/Write/Edit/MultiEdit | Captura de eventos de gobernanza desde output |
| **post:session-activity-tracker** | Cualquiera | Seguimiento de llamadas a herramientas y actividad de archivos |
| **post:observe:continuous-learning** | Cualquiera | Captura de resultados para aprendizaje |
| **post:ecc-metrics-bridge** | Cualquiera | Agregación de métricas de sesión |
| **post:ecc-context-monitor** | Cualquiera | Advertencias de agotamiento de contexto/costo/scope creep |
| **post-bash-build-complete** | Bash | Notificación de build completo |
| **post-bash-command-log** | Bash | Log de comandos bash |
| **post-bash-dispatcher** | Bash | Dispatcher post-bash |
| **post-bash-pr-created** | Bash | Notificación de PR creado |
| **post-edit-accumulator** | Edit | Acumulador post-edit |
| **post-edit-console-warn** | Edit | Advertencia de console.log |
| **post-edit-format** | Edit | Formateo post-edit |
| **post-edit-typecheck** | Edit | Typecheck post-edit |

#### SessionStart (4 hooks)

| Hook | Función |
|------|---------|
| **session:start** | Carga de contexto previo, detección de package manager |
| **session-start.js** | Inicialización de sesión |
| **session-start-bootstrap.js** | Bootstrap de sesión |
| **cursor-session-env.js** | Configuración de entorno para Cursor |

#### SessionEnd (3 hooks)

| Hook | Función |
|------|---------|
| **session:end:marker** | Marcador no bloqueante de fin de sesión |
| **session-end.js** | Persistencia de estado de sesión |
| **session-end-marker.js** | Marcador de fin de sesión |

#### Stop (6 hooks)

| Hook | Función |
|------|---------|
| **stop:format-typecheck** | Formateo batch + typecheck de todos los JS/TS editados |
| **stop:check-console-log** | Verificación de console.log en archivos modificados |
| **stop:session-end** | Persistencia de estado de sesión |
| **stop:evaluate-session** | Extracción de patrones de la sesión |
| **stop:cost-tracker** | Seguimiento de tokens y costos |
| **stop:desktop-notify** | Notificación de escritorio (macOS/WSL) |

#### PreCompact (2 hooks)

| Hook | Función |
|------|---------|
| **pre:compact** | Guardado de estado antes de compactación |
| **pre-compact.js** | Script de pre-compactación |

### 6.3 Tipos de Automatizaciones

| Tipo | Descripción | Ejemplos |
|------|-------------|----------|
| **Guardrails** | Bloques preventivos | config-protection, gateguard, block-no-verify |
| **Quality Gates** | Control de calidad post-acción | quality-gate, design-quality-check |
| **Observabilidad** | Monitoreo y métricas | context-monitor, metrics-bridge, activity-tracker |
| **Aprendizaje** | Extracción de patrones | continuous-learning, evaluate-session, observe-runner |
| **Seguridad** | Escaneo y protección | governance-capture, insaits-security-monitor, security-scan |
| **DevOps** | Automatización de entorno | tmux-reminder, git-push-reminder, dev-server-block |
| **Mantenimiento** | Formateo y limpieza | format-typecheck, console-warn, edit-accumulator |
| **Notificaciones** | Alertas al usuario | desktop-notify, build-complete, pr-created |
| **MCP** | Salud de servidores MCP | mcp-health-check |

---

## 7. Workflows

### 7.1 Workflow Nativo: `orch-review.workflow.js`

Workflow nativo de Claude Code para la fase de revisión del pipeline ORCH (Fase 5).

**Fases del workflow:**
1. **Revisión multi-dimensión paralela**: code-reviewer + language-reviewer (según lenguaje) + security-reviewer (condicional)
2. **Verificación adversarial**: Cada hallazgo CRITICAL/HIGH es verificado adversarialmente
3. **Veredicto**: Retorna `APPROVE` o `CHANGES_REQUESTED` con hallazgos bloqueantes y advisory para Gate 2

---

## 8. Análisis Forense de Seguridad

### 8.1 Resumen de Hallazgos

| Categoría | Riesgo | Cantidad | Estado |
|-----------|--------|----------|--------|
| Secretos hardcodeados |  Crítico | 0 | PASS: No encontrados |
| Código malicioso / malware |  Crítico | 0 | PASS: No encontrado |
| Código ofuscado |  Alto | 0 | PASS: No encontrado |
| Exfiltración de datos |  Alto | 0 | PASS: No encontrada |
| Inyección de comandos |  Alto | 0 | PASS: No encontrada |
| Cryptominers / backdoors |  Crítico | 0 | PASS: No encontrados |
| Datos personales expuestos (PII) |  Medio | **2** | WARNING: Ver detalle |
| Claves de prueba en tests |  Bajo | ~8 | PASS: Solo fixtures |
| Dependencias con CVEs conocidas |  Medio | 0 | PASS: Overrides para markdown-it y js-yaml |

### 8.2 Hallazgos Detallados

#### Medio: PII expuesta en documentación

| Archivo | Líneas | Contenido |
|---------|--------|-----------|
| `docs/fixes/HOOK-FIX-20260421.md` | 21, 63, 131-132 | `C:\Users\sugig\.claude\settings.local.json` |
| `docs/fixes/HOOK-FIX-20260421-ADDENDUM.md` | 107-109 | `C:\Users\sugig\Documents\...` |

**Recomendación:** Reemplazar `sugig` por `<user>` en ambos archivos.

### 8.3 Prácticas de Seguridad Verificadas

| Práctica | Estado |
|----------|--------|
| `.gitignore` cubre `.env*`, `*.key`, `secrets.json` | PASS: Correcto |
| `.env.example` con valores placeholder | PASS: Correcto |
| `.gitleaksignore` configurado | PASS: Correcto |
| Secretos en CI/CD via `${{ secrets.* }}` | PASS: Correcto |
| Acciones de GitHub pinned por SHA | PASS: Correcto |
| `persist-credentials: false` en workflows | PASS: Correcto |
| `npm audit --audit-level=high` en CI | PASS: Correcto |
| Escaneo de IOC en supply chain | PASS: Correcto |
| Validación de rutas personales en CI | PASS: Correcto |
| OIDC para npm provenance | PASS: Correcto |

### 8.4 Herramientas de Seguridad Integradas

| Herramienta | Propósito |
|-------------|-----------|
| **AgentShield** | Auditor de configuraciones de agentes IA (102 reglas, 1282 tests) |
| **Gitleaks** | Detección de secretos en el repositorio |
| **InsAIts Security Monitor** | Monitoreo de seguridad en tiempo real en hooks |
| **Supply-chain IOC Scanner** | Detección de paquetes comprometidos conocidos |
| **Governance Capture** | Captura de eventos de gobernanza |
| **Config Protection** | Bloqueo de cambios no autorizados a configuraciones |
| **Security Scan Skill** | Escaneo de seguridad OWASP Top 10 |

---

## 9. Resumen de Infraestructura

### 9.1 Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| **Lenguaje principal** | JavaScript (Node.js >=18) |
| **Package manager** | Yarn 4.9.2 |
| **Runtime secundario** | Python >=3.11 |
| **Control plane** | Rust (ecc2/) |
| **Dashboard** | Python Tkinter |
| **Base de datos** | SQLite (via sql.js y rusqlite) |
| **LLM Abstraction** | Python (anthropic, openai) |
| **Testing** | Node (c8 coverage) + Python (pytest) |
| **Linting** | ESLint + Markdownlint |

### 9.2 Dependencias de Producción

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| `@iarna/toml` | ^2.2.5 | Parseo de TOML |
| `ajv` | ^8.20.0 | Validación de esquemas JSON |
| `sql.js` | ^1.14.1 | SQLite en WASM para state store |

### 9.3 Dependencias de Desarrollo

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| `@eslint/js` | ^9.39.2 | Linter |
| `@opencode-ai/plugin` | ^1.16.2 | Plugin SDK para OpenCode |
| `@types/node` | 25.9.2 | Tipos de Node |
| `c8` | ^11.0.0 | Cobertura de código |
| `eslint` | ^10.6.0 | Linter |
| `globals` | ^17.4.0 | Globals de ESLint |
| `markdownlint-cli` | ^0.48.0 | Linter de Markdown |
| `typescript` | ^6.0.3 | TypeScript |

### 9.4 Rust Control Plane (ecc2/)

| Dependencia | Propósito |
|-------------|-----------|
| ratatui + crossterm | TUI dashboard |
| tokio | Async runtime |
| rusqlite | SQLite state store |
| git2 | Integración Git |
| clap | CLI argument parsing |
| serde / serde_json / toml | Serialización |
| chrono + cron | Tiempo y scheduling |
| uuid | IDs de sesión |
| ureq | HTTP client |
| sha2 | Hashing |

---

## 10. Conclusiones

### 10.1 Fortalezas

1. **Ecosistema completo**: 67 agentes, 278 skills, 93 comandos y 49 hooks cubren prácticamente todas las necesidades de desarrollo de software asistido por IA
2. **Multi-harness**: Funciona en Claude Code, Codex, Cursor, OpenCode, Gemini, Zed y más
3. **Multi-lenguaje**: Soporte para 22+ lenguajes de programación con rules, reviewers y build resolvers dedicados
4. **Seguridad robusta**: Múltiples capas de seguridad (AgentShield, gitleaks, governance capture, config protection)
5. **Aprendizaje continuo**: Sistema de instintos que mejora con el uso
6. **Arquitectura extensible**: Skills, agents y hooks son fáciles de añadir
7. **CI/CD profesional**: Workflows de GitHub con pinned SHAs, permisos mínimos, OIDC
8. **Código limpio y seguro**: Sin malware, sin ofuscación, sin secretos expuestos

### 10.2 Áreas de Mejora

1. **PII en documentación**: 2 archivos contienen rutas personales de Windows del desarrollador (`C:\Users\sugig\...`)
2. **Pruebas de seguridad adicionales**: Se recomienda `cargo audit` para el subproyecto Rust `ecc2/`
3. **Portabilidad Windows**: Algunas rutas hardcodeadas a `/bin/sh` en el código Rust no son portables a Windows

### 10.3 Verificación de Seguridad

```
 CRÍTICAS:   0
 ALTAS:      0
 MEDIAS:     2 (PII en documentación)
 BAJAS:      ~8 (claves de prueba en fixtures)
PASS: INFO:       Múltiples herramientas de seguridad integradas
```

**Puntaje de seguridad general: A-** (casi perfecto, con mínima exposición de PII en documentación)

---

*Reporte generado el 2026-07-08 por análisis forense automatizado.*
*Repositorio: https://github.com/affaan-m/ECC*
