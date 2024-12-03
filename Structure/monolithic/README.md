# Monolith Django Starter

## Introduction
This project serves as a starter Django repository designed for majestic monolith architecture. The primary goal is to provide a scaffolded structure and sample architecture for quickly prototyping scalable backend API servers. Drawing inspiration from the concept of the [Majestic Monolith](https://m.signalvnoise.com/the-majestic-monolith/) and principles outlined in [Two Scoops of Django](https://www.feldroy.com/books/two-scoops-of-django-3-x), this starter code is geared towards building scalable applications for small to mid-sized teams.

## Why Majestic Modular Monolith?
While microservices are gaining popularity, they may be overwhelming for solo developers or small to medium-scale projects. This starter project, embracing Domain-Driven Design (DDD) practices with code and data isolation, aims to prepare for scalability without the immediate need for microservices. The Majestic Monolith Django (MMD) approach can reduce cognitive load and simplify coordination.

## Sample Application
The repository includes a sample application with four modules (`auth`, `user`, `shipping`, `distribution`). The modular monolith structure is illustrated with an ERD (Entity-Relationship Diagram). API documentation can be accessed via `/api/docs/redoc` (login as staff required).

## Infrastructure
The project recommends using a separate CDK (Cloud Development Kit) repository for deployment. The CDK includes modules for ECS cluster with Django and Nginx images, EventBridge, Aurora for MySQL, and ALB (Application Load Balancer). Refer to [infra setup](docs/infra_setup.md) for more details.

## Features
- Cache: Redis
- Authentication: JWT
- API Documentation: drf-spectacular
- CI/CD: GitHub Actions with precommit and pytest using Docker Compose
- Libraries: Django, djangorestframework, django-storages, and more (refer to [pyproject.toml](/DRF/APIResponse/custom_response.py#L15))

## How to Setup
Refer to [setup](docs/setup.md) for setup instructions.

## Contribution
Feedback and contributions are welcome. Help improve the project and make it more robust.

## Reference
- [Majestic Monolith](https://m.signalvnoise.com/the-majestic-monolith/)
- [Majestic Modular Monoliths](https://lukashajdu.com/post/majestic-modular-monolith/)
- [Two Scoops of Django 3.x](https://www.feldroy.com/books/two-scoops-of-django-3-x)
- [Cookie-cutter-django](https://github.com/cookiecutter/cookiecutter-django)

# Cookie-cutter
Use cookie cutter to start a new project:
 - https://github.com/kokospapa8/majestic-monolith-django.git --checkout cookie-cutter


# Release
## Version
- 0.1.0: Initial application update with API
- 0.2.0: Cookie cutter integration
- 0.2.1: drf-spectacular update

## Release Plan
- 0.3.0: Async support (planned)
