#include <SofaCaribou/config.h>
#include <SofaCaribou/Material/SaintVenantKirchhoffMaterial.h>
#include <SofaCaribou/Material/NeoHookeanMaterial.h>
#include <SofaCaribou/FEniCS/Material/SaintVenantKirchhoffMaterial_FEniCS.h>



DISABLE_ALL_WARNINGS_BEGIN
#include <sofa/core/ObjectFactory.h>
DISABLE_ALL_WARNINGS_END

using namespace sofa::core;
using namespace caribou::geometry;
using namespace caribou;

namespace SofaCaribou::material {

template class SaintVenantKirchhoffMaterial_FEniCS<caribou::geometry::Tetrahedron<caribou::Linear>, sofa::defaulttype::Vec3Types>;
template class SaintVenantKirchhoffMaterial_FEniCS<caribou::geometry::Hexahedron<caribou::Quadratic>, sofa::defaulttype::Vec3Types>;

static int SaintVenantKirchhoffClass = RegisterObject("Caribou Saint-Venant-Kirchhoff hyperelastic material")
//                                                 .add< SaintVenantKirchhoffMaterial<sofa::defaulttype::Vec1Types> >()
//                                                 .add< SaintVenantKirchhoffMaterial<sofa::defaulttype::Vec2Types> >()
                                                 .add< SaintVenantKirchhoffMaterial<sofa::defaulttype::Vec3Types> >();

static int SaintVenantKirchhoffFEniCSClass = RegisterObject("FEniCS Saint-Venant-Kirchhoff hyperelastic material")
                                                 .add< SaintVenantKirchhoffMaterial_FEniCS< Tetrahedron<Linear>, sofa::defaulttype::Vec3Types> >()
//                                                 .add< SaintVenantKirchhoffMaterial_FEniCS<sofa::defaulttype::Vec3Types, caribou::geometry::Tetrahedron<caribou::Quadratic>> >()
//                                                 .add< SaintVenantKirchhoffMaterial_FEniCS<sofa::defaulttype::Vec3Types, caribou::geometry::Hexahedron<caribou::Linear>> >()
                                                 .add< SaintVenantKirchhoffMaterial_FEniCS<Hexahedron<Quadratic>, sofa::defaulttype::Vec3Types> >();

static int NeoHookeanClass = RegisterObject("Caribou NeoHookeanMaterial hyperelastic material")
//    .add< NeoHookeanMaterial<sofa::defaulttype::Vec1Types> >()
//    .add< NeoHookeanMaterial<sofa::defaulttype::Vec2Types> >()
    .add< NeoHookeanMaterial<sofa::defaulttype::Vec3Types> >();

} // namespace SofaCaribou::material
