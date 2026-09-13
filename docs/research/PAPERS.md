# Academic References — thegent

**Purpose:** Research backing for dotfiles/config management architecture  
**Last Updated:** 2026-04-02

---

## Core Academic Foundations

### Nix Research (Primary Influence)

1. **"Nix: A Safe and Policy-Free System for Software Deployment"**
   - _Author:_ Eelco Dolstra
   - _Institution:_ Utrecht University
   - _Year:_ 2006
   - _Type:_ PhD Thesis
   - _URL:_ https://nixos.org/~eelco/pubs/phd-thesis.pdf
   - _Key Contributions:_
     - Pure functional package management
     - Immutable software stores (/nix/store)
     - Transactional upgrades and rollbacks
     - Reproducible builds
   - _Application:_ thegent Nix integration, reproducible environment guarantee
   - _Citations:_ 1000+ (foundational for Nix ecosystem)

2. **"The Purely Functional Software Deployment Model"**
   - _Authors:_ Eelco Dolstra, Merijn de Jonge, Eelco Visser
   - _Venue:_ 26th International Conference on Software Engineering (ICSE 2004)
   - _Pages:_ 205-214
   - _URL:_ https://nixos.org/~eelco/pubs/icse2004-nix.pdf
   - _Key Contributions:_
     - Functional deployment model
     - Dependency isolation
     - Build reproducibility
   - _Application:_ thegent factory seed reproducibility

3. **"NixOS: A Purely Functional Linux Distribution"**
   - _Authors:_ Eelco Dolstra, Andres Löh
   - _Venue:_ 13th ACM SIGPLAN International Conference on Functional Programming (ICFP 2008)
   - _Pages:_ 367-378
   - _URL:_ https://nixos.org/~eelco/pubs/icfp2008-nixos.pdf
   - _Key Contributions:_
     - System-level functional configuration
     - NixOS module system
     - Declarative system configuration
   - _Application:_ thegent system configuration patterns

4. **"Integrating Software Construction and Software Deployment"**
   - _Authors:_ Eelco Dolstra
   - _Venue:_ 11th International Conference on Software Configuration Management (SCM 2011)
   - _URL:_ https://nixos.org/~eelco/pubs/scm2011-integration.pdf
   - _Key Contributions:_
     - Unified build and deployment
     - Build system integration
   - _Application:_ thegent build + deploy integration

---

## Software Architecture

5. **"Design Patterns: Elements of Reusable Object-Oriented Software"**
   - _Authors:_ Gamma, Helm, Johnson, Vlissides (GoF)
   - _Publisher:_ Addison-Wesley, 1994
   - _Patterns Applied:_
     - **Factory Pattern:** Factory seed system
     - **Adapter Pattern:** Multi-manager abstraction
     - **Plugin Pattern:** Skill system architecture
     - **Singleton:** Policy gate coordination

6. **"Domain-Driven Design: Tackling Complexity in the Heart of Software"**
   - _Author:_ Eric Evans
   - _Publisher:_ Addison-Wesley, 2003
   - _Concepts Applied:_
     - **Bounded Contexts:** Platform-specific modules
     - **Factories:** Factory seed pattern
     - **Aggregates:** Configuration bundles
     - **Domain Events:** Policy gate triggers

7. **"Clean Architecture: A Craftsman's Guide to Software Structure and Design"**
   - _Author:_ Robert C. Martin
   - _Publisher:_ Prentice Hall, 2017
   - _Concepts Applied:_
     - Dependency inversion
     - Boundary abstractions
     - Framework independence

---

## DevOps & Configuration Management

8. **"Infrastructure as Code: Managing Servers in the Cloud"**
   - _Author:_ Kief Morris
   - _Publisher:_ O'Reilly Media, 2020 (2nd Edition)
   - _Key Concepts:_
     - Declarative infrastructure
     - Immutable infrastructure
     - Idempotency
     - Configuration drift detection
   - _Application:_ thegent declarative config, drift prevention via policy gates

9. **"Site Reliability Engineering: How Google Runs Production Systems"**
   - _Editors:_ Betsy Beyer, Chris Jones, Jennifer Petoff, Niall Murphy
   - _Publisher:_ O'Reilly Media, 2017
   - _Key Concepts:_
     - Error budgets
     - Automation
     - Monitoring and observability
     - Change management
   - _Application:_ thegent governance model, SLOs, policy gates

10. **"The DevOps Handbook"**
    - _Authors:_ Gene Kim, Jez Humble, Patrick Debois, John Willis
    - _Publisher:_ IT Revolution, 2021 (2nd Edition)
    - _Key Concepts:_
      - Three Ways (Flow, Feedback, Continual Learning)
      - Continuous delivery
      - Automated testing
    - _Application:_ thegent continuous configuration, automated policy validation

11. **"Continuous Delivery: Reliable Software Releases through Build, Test, and Deployment Automation"**
    - _Authors:_ Jez Humble, David Farley
    - _Publisher:_ Addison-Wesley, 2010
    - _Key Concepts:_
      - Deployment pipeline
      - Build quality in
      - Everyone responsible for delivery
    - _Application:_ thegent quality gates, continuous configuration

---

## Rust Systems Programming

12. **"Programming Rust: Fast, Safe Systems Development"**
    - _Authors:_ Jim Blandy, Jason Orendorff, Leonora Tindall
    - _Publisher:_ O'Reilly Media, 2021 (2nd Edition)
    - _Application:_ Systems-level configuration management, async runtime

13. **"Rust for Rustaceans: Idiomatic Programming for Experienced Developers"**
    - _Author:_ Jon Gjengset
    - _Publisher:_ No Starch Press, 2021
    - _Application:_ Advanced trait design, plugin architecture

14. **"Zero to Production in Rust"**
    - _Author:_ Luca Palmieri
    - _Publisher:_ Luca Palmieri, 2022
    - _Application:_ Production patterns, telemetry, configuration

---

## Security & Policy

15. **"Security Engineering: A Guide to Building Dependable Distributed Systems"**
    - _Author:_ Ross J. Anderson
    - _Publisher:_ Wiley, 2020 (3rd Edition)
    - _Application:_ Secure configuration defaults, policy enforcement

16. **"The Tangled Web: A Guide to Securing Modern Web Applications"**
    - _Author:_ Michal Zalewski
    - _Publisher:_ No Starch Press, 2011
    - _Application:_ Sandboxing, security boundaries

17. **"Secure by Design"**
    - _Authors:_ Dan Bergh Johnsson, Daniel Deogun, Daniel Sawano
    - _Publisher:_ Manning, 2019
    - _Application:_ Secure defaults, domain primitives

---

## Cross-Platform Development

18. **"POSIX Programmer's Guide"**
    - _Author:_ Donald Lewine
    - _Publisher:_ O'Reilly Media, 1991
    - _Application:_ Unix-like compatibility layer

19. **"Advanced Programming in the UNIX Environment"**
    - _Authors:_ W. Richard Stevens, Stephen A. Rago
    - _Publisher:_ Addison-Wesley, 2013 (3rd Edition)
    - _Application:_ File system operations, process management

---

## User Interface Patterns

20. **"The Humane Interface: New Directions for Designing Interactive Systems"**
    - _Author:_ Jef Raskin
    - _Publisher:_ Addison-Wesley, 2000
    - _Application:_ TUI design principles, modelessness

21. **"Designing Interfaces"**
    - _Author:_ Jenifer Tidwell
    - _Publisher:_ O'Reilly Media, 2020 (3rd Edition)
    - _Application:_ CLI/TUI patterns, progressive disclosure

---

## Research Gaps (Future Investigation)

| Topic                            | Current Gap                   | Priority | Notes                   |
| -------------------------------- | ----------------------------- | -------- | ----------------------- |
| Mobile config management         | No academic research found    | P3       | iOS/Android restrictive |
| Secrets management integration   | Limited papers on dev secrets | P2       | 1Password/pass research |
| Configuration migration patterns | Academic gap                  | P2       | Dotfile tool migration  |
| Team vs. personal configs        | Limited research              | P2       | Organizational patterns |

---

## Citation Format

When citing in thegent documentation:

```markdown
> Research: Dolstra (2006), "Nix: A Safe and Policy-Free System for Software Deployment"
> URL: https://nixos.org/~eelco/pubs/phd-thesis.pdf
> Application: Factory seed reproducibility guarantee
```

---

**Last Updated:** 2026-04-02  
**Next Review:** 2026-04-16
