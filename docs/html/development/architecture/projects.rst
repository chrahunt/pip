Projects are the entities that pip downloads and prepares to get information.

A ParsedRequirement represents not just the parsed information but also contextual
information, like settings or something that a user would have associated with
the input requirement.


Pip supports a number of different project types.

Each of these project types has different ways of getting information.

In general we do not want to do work needlessly.

There are PEP 517 entities and legacy entites.

The various PEPs dictate what kinds of information we can get from these different inputs.

Once we have parsed an input requirement we convert it to a project.

Each project is represented by a class in ``projects.projects``.

The ``projects.factory.ProjectFactory`` is responsible for mapping the
parsed requirement to the project class itself.

Given a parsed requirement, the project factory derives a set of traits
that represent the project. The available traits are in ``projects.traits``.
Once we have the applicable traits those are queried in the ``projects.registry.ProjectTypeRegistry``.

We have helper functions in ``projects.registry`` which are used to register the classes.

The classes provide a ``traits`` member which indicates the traits applicable to the
type. The ``projects.registry.ConstructibleProject`` type provides the type checking
to ensure that the traits and the ``from_req`` method are defined.

There are 3 pieces of shared state that the projects need:

1. Global configuration - this is configuration that may be passed by the user
   and would have an impact on the processing of the project, like isolation or
   build options that apply to everything
2. package-specific configuration - these configuration parameters would apply
   on a package-by-package basis. This would be like format-control or build/global
   options
3. services - these are the helpers that require initialization (like the PipSession)
   but provide a capability to the projects as opposed to a configuration parameter that
   would be read by the project and then impact its behavior

these pieces of shared state are passed from project to project. The helpers in
``projects.context`` try to reduce some of the boilerplate related to that.

When a project doesn't provide some capability it can be "prepared" in order to
transform it into another form of the project that may provide the requested information.
Preparation can involve:

1. Downloading
2. Building a wheel or invoking some command

The preparation should be transparent to the actual code that is using the project, so we
wrap projects in a ``projects.proxy.ProxyProject`` which provides the same interface as
a normal project but then internally will prepare the project if the requested information
is not available from the project in its current form.
