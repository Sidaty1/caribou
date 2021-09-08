#include <SofaCaribou/Mapping/CaribouBarycentricMapping.h>
#include <Caribou/Geometry/Hexahedron.h>

DISABLE_ALL_WARNINGS_BEGIN
#include <sofa/version.h>
#include <sofa/core/Mapping.inl>
#include <sofa/simulation/Node.h>
#include <sofa/core/visual/VisualParams.h>
DISABLE_ALL_WARNINGS_END

#if (defined(SOFA_VERSION) && SOFA_VERSION < 201200)
namespace sofa { using Index = unsigned int; }
#endif

#if (defined(SOFA_VERSION) && SOFA_VERSION < 210699)
namespace sofa::type {
using RGBAColor = ::sofa::type::RGBAColor;
using Vector3 = ::sofa::type::Vector3;
}
#endif

namespace SofaCaribou::mapping {

namespace {
template <typename T> struct is_rigid_types {static constexpr bool value = false;};
template <sofa::Size N, typename real> struct is_rigid_types<sofa::defaulttype::StdRigidTypes<N, real>> {static constexpr bool value = true;};
template <typename T> static constexpr auto is_rigid_types_v = is_rigid_types<T>::value;
}

template<typename Element, typename MappedDataTypes>
CaribouBarycentricMapping<Element, MappedDataTypes>::CaribouBarycentricMapping()
: d_topology(initLink("topology", "Topology that contains the embedding (parent) elements."))
{  
}

template<typename Element, typename MappedDataTypes>
void CaribouBarycentricMapping<Element, MappedDataTypes>::init() {
    using CaribouTopology = SofaCaribou::topology::CaribouTopology<Element>;

    // Get the topology if it is not already provided by the user
    if (d_topology.empty()) {
        auto * context_node = dynamic_cast<sofa::simulation::Node*>(this->getContext());
        auto * parent_context_node = (context_node->getNbParents() > 0) ? context_node->getFirstParent() : nullptr;
        CaribouTopology * topology = nullptr;

        // Search first in the parent context node (if any)
        if (parent_context_node) {
            topology = parent_context_node->getContext()->get<CaribouTopology>();
        }

        // If not found in the parent context, search in the current context
        if (not topology and (context_node != parent_context_node)) {
            topology = context_node->getContext()->get<CaribouTopology>();
        }

        if (not topology) {
            msg_error()
                    << "Could not find a topology container in the parent context node, or the current context node. "
                    << "Please add a '" << CaribouTopology::GetClass()->typeName << "' component to your scene, and set its "
                    << "complete path in the '" << d_topology.getName() << "' data attribute.";
            return;
        }
        // We got one, use it
        d_topology.set(topology);
        msg_info() << "Topology automatically found at '" << topology->getPathName() << "'";
    } else if (not d_topology.get()) {
        msg_error() << "The '" << d_topology.getName() << "' data field does not point towards a valid topology container.";
        return;
    }

    // Quick sanity checks
    if (not d_topology->domain()) {
        msg_error() << "The topology '" << d_topology->getPathName() << "' doesn't seem to have been initialized, or "
                    << "might not contain any elements.";
        return;
    }

    if (this->getFromModel()->getSize() == 0) {
        msg_error() << "The parent mechanical object '" << this->getFromModel()->getPathName() << "' doesn't contain any nodes.";
        return;
    }

    if (this->getToModel()->getSize() == 0) {
        msg_error() << "The mapped mechanical object '" << this->getToModel()->getPathName() << "' doesn't contain any nodes.";
        return;
    }

    // Initialize the rest positions
    if (this->getToModel()->readRestPositions().empty()) {
        auto mapped_rest_positions = this->getToModel()->writeOnlyRestPositions();
        auto mapped_positions = this->getToModel()->readPositions();
        mapped_rest_positions.resize(mapped_positions.size());
        for (sofa::Index i = 0; i < mapped_positions.size(); ++i) {
            mapped_rest_positions[i] = mapped_positions[i];
        }
    }

    // Create the barycentric container

    auto mapped_rest_positions =
        Eigen::Map<const Eigen::Matrix<MappedScalar, Eigen::Dynamic, MappedDimension, Eigen::RowMajor>, 
                    Eigen::Unaligned, 
                    Eigen::Stride<MapTotalSize, 1>
                > (
                this->getToModel()->readRestPositions()[0].ptr(),
                this->getToModel()->readRestPositions().size(),
                MappedDimension
        );
    p_barycentric_container.reset(new caribou::topology::BarycentricContainer<Domain>(d_topology->domain()->embed(mapped_rest_positions)));

    if (not p_barycentric_container->outside_nodes().empty()) {
        const auto n = p_barycentric_container->outside_nodes().size();
        msg_error() << n << " / " << mapped_rest_positions.rows() << " "
                      << "mapped nodes were found outside of the embedding topology, i.e., they are not "
                      << "contained inside any elements. Every nodes must be found inside the domain.";
        return;
    }

    // Precompute the mapping matrix (derivative of the mapping function w.r.t rest position).
    p_J.setZero(); // Let's clear it just in case init was called previously
    p_J.resize(this->getToModel()->getSize(), this->getFromModel()->getSize());
    std::vector<Eigen::Triplet<Scalar>> entries;
    entries.reserve(this->getFromModel()->getSize());
    const auto * domain = d_topology->domain();
    const auto & barycentric_points = p_barycentric_container->barycentric_points();
    for (std::size_t i = 0; i < barycentric_points.size(); ++i) {
        const auto & bp = barycentric_points[i];
        const auto & node_indices = domain->element_indices(bp.element_index);
        const auto e = domain->element(bp.element_index);
        const auto L = e.L(bp.local_coordinates); // Shape functions at barycentric coordinates
        for (Eigen::Index j = 0; j < node_indices.rows(); ++j) {
            const auto & node_index = node_indices[j];
            entries.emplace_back(i, node_index, L[j]);
        }
    }
    p_J.setFromTriplets(entries.begin(), entries.end());

    // This is needed to map the initial nodal positions and velocities (and, optionally, rest positions).
    Inherit1 ::init();
}

template<typename Element, typename MappedDataTypes>
void CaribouBarycentricMapping<Element, MappedDataTypes>::apply(const sofa::core::MechanicalParams * /*mparams*/,
                                                                MappedDataVecCoord & data_output_mapped_position,
                                                                const DataVecCoord & data_input_position) {
    
    
    // Sanity check
    if (not p_barycentric_container or not p_barycentric_container->outside_nodes().empty()) {
        return;
    }

    const auto & barycentric_points = p_barycentric_container->barycentric_points();
    const auto nb_of_barycentric_points = barycentric_points.size();

    // Container (parent) nodes
    auto input_position = sofa::helper::ReadAccessor<DataVecCoord>(data_input_position);
    auto positions =
            Eigen::Map<const Eigen::Matrix<Scalar, Eigen::Dynamic, Dimension, Eigen::RowMajor>> (
                    input_position[0].ptr(),
                    input_position.size(),
                    Dimension
            );
            
    // Mapped (embedded) nodes
    auto output_mapped_position = sofa::helper::WriteOnlyAccessor<MappedDataVecCoord>(data_output_mapped_position);
    auto mapped_positions =
        Eigen::Map<Eigen::Matrix<MappedScalar, Eigen::Dynamic, MappedDimension, Eigen::RowMajor>, 
                    Eigen::Unaligned, 
                    Eigen::Stride<MapTotalSize, 1>
                > (
                output_mapped_position[0].ptr(),
                output_mapped_position.size(),
                MappedDimension
                /* Eigen::Stride<MapTotalSize, 1>(MapTotalSize, 1) */
        );
    
    Eigen::MatrixXd mapped_rotations(output_mapped_position.size(), 4);
    
    for(int i = 0; i < output_mapped_position.size(); ++i) {
        for(int j = 0; j < 4; ++j) {
            mapped_rotations(i, j) = output_mapped_position[i][j+3];
        }
    } 
    

    if constexpr (is_rigid_types_v<MappedDataTypes>) {
        
        /* std::cout << "Debut: " << std::endl;
        std::cout << mapped_rotations << std::endl; */

        for (std::size_t i = 0; i <nb_of_barycentric_points; ++i) {
            const auto & bp = barycentric_points[i];
            
            const auto & element_index = bp.element_index;
            const auto & local_coordinates = bp.local_coordinates;
            const auto elem = d_topology->element(element_index, data_input_position);
            
            const auto new_positions = elem.world_coordinates(local_coordinates);
            
            auto rotation = elem.frame(local_coordinates);
            //std::cout << rotation << std::endl;

            Eigen::Quaterniond q;
            q = rotation;

            // Coordinates part of the DOFs
            for (std::size_t j = 0; j < Dimension; ++j) {
                mapped_positions(i, j) = new_positions[j]; 
            }

            // Rotation part of the DOFs
            mapped_positions(i, Dimension+0) = mapped_rotations(i, 0); // q.x();
            mapped_positions(i, Dimension+1) = mapped_rotations(i, 1); // q.y();
            mapped_positions(i, Dimension+2) = mapped_rotations(i, 2); // q.z(); 
            mapped_positions(i, Dimension+3) = mapped_rotations(i, 3); // q.w();

        }
    } else {
        // Interpolate the parent positions onto the mapped nodes
        p_barycentric_container->interpolate(positions, mapped_positions);
    } 

    /* std::cout << mapped_positions << std::endl; */
}


template<typename Element, typename MappedDataTypes>
void CaribouBarycentricMapping<Element, MappedDataTypes>::applyJ(const sofa::core::MechanicalParams * /*mparams*/,
                                                                 MappedDataVecDeriv & data_output_mapped_velocity,
                                                                 const DataVecDeriv & data_input_velocity) {
    // Sanity check
    if (not p_barycentric_container or not p_barycentric_container->outside_nodes().empty()) {
        return;
    }

    // Container (parent) nodes
    auto input_velocities = sofa::helper::ReadAccessor<DataVecDeriv>(data_input_velocity);
    auto velocities =
            Eigen::Map<const Eigen::Matrix<Scalar, Eigen::Dynamic, Dimension, Eigen::RowMajor>> (
                    input_velocities[0].ptr(),
                    input_velocities.size(),
                    Dimension
            );

    // Mapped (embedded) nodes
    auto output_mapped_position = sofa::helper::WriteOnlyAccessor<MappedDataVecDeriv>(data_output_mapped_velocity);
    auto mapped_velocities =
            Eigen::Map<Eigen::Matrix<MappedScalar, Eigen::Dynamic, MappedDimension, Eigen::RowMajor>> (
                    output_mapped_position[0].ptr(),
                    output_mapped_position.size(),
                    MappedDimension
            );

    // Interpolate the parent positions onto the mapped nodes
    p_barycentric_container->interpolate(velocities, mapped_velocities);
}

template<typename Element, typename MappedDataTypes>
void CaribouBarycentricMapping<Element, MappedDataTypes>::applyJT(const sofa::core::MechanicalParams * /*mparams*/,
                                                                  DataVecDeriv & data_output_force,
                                                                  const MappedDataVecDeriv & data_input_mapped_force) {
    // Sanity check
    if (not p_barycentric_container or not p_barycentric_container->outside_nodes().empty()) {
        return;
    }

    // Container (parent) nodes
    auto output_forces = sofa::helper::WriteAccessor<DataVecDeriv>(data_output_force);
    auto forces =
            Eigen::Map<Eigen::Matrix<Scalar, Eigen::Dynamic, Dimension, Eigen::RowMajor>> (
                    output_forces[0].ptr(),
                    output_forces.size(),
                    Dimension
            );
    
    // Mapped (embedded) nodes
    auto input_mapped_forces = sofa::helper::ReadAccessor<MappedDataVecDeriv>(data_input_mapped_force);
    auto mapped_forces =
        Eigen::Map<const Eigen::Matrix<MappedScalar, Eigen::Dynamic, MappedDimension, Eigen::RowMajor>, 
                         Eigen::Unaligned, 
                         Eigen::Stride<MapForce, 1>
                > (
                input_mapped_forces[0].ptr(),
                input_mapped_forces.size(),
                MappedDimension
                /* Eigen::Stride<MapTotalSize, 1>(MapTotalSize, 1) */
        );

    const auto number_of_nodes = p_J.transpose().rows();
    const auto number_of_elements =d_topology->number_of_elements(); // nomber of element
    const auto & barycentric_points = p_barycentric_container->barycentric_points();
    const auto nb_of_barycentric_points = barycentric_points.size();

    // Container (parent) nodes
    auto input_position = sofa::helper::ReadAccessor<DataVecCoord>(this->getFromModel()->readPositions());
    auto positions =
    Eigen::Map<const Eigen::Matrix<Scalar, Eigen::Dynamic, Dimension, Eigen::RowMajor>> (
        input_position[0].ptr(),
        input_position.size(),
        Dimension
    );

    Eigen::MatrixXd mapped_torques(nb_of_barycentric_points, 3);
    
    for(int i = 0; i < input_mapped_forces.size(); ++i) {
        for(int j = 0; j < 3; ++j) {
            mapped_torques(i, j) = float(input_mapped_forces[i][j+3]);
        }
    } 

    const auto prod = p_J.transpose() * mapped_torques; 

    Eigen::MatrixXd torques_to_linear_forces(number_of_nodes, 3);
    for(int i = 0; i < positions.rows(); ++i) {
        Eigen::Vector3d v = prod.row(i).transpose();
        Eigen::Vector3d w = positions.row(i).transpose();
        torques_to_linear_forces.row(i) =  v.cross(w).transpose();
    } 

    if constexpr (is_rigid_types_v<MappedDataTypes>) { 
        // Inverse mapping using the transposed of the Jacobian matrix and converting torques to linear forces
        forces.noalias() += p_J.transpose() * mapped_forces - torques_to_linear_forces;  
    } else {
        // Inverse mapping using the transposed of the Jacobian matrix
        forces.noalias() += p_J.transpose() * mapped_forces;
    }
}

template<typename Element, typename MappedDataTypes>
void CaribouBarycentricMapping<Element, MappedDataTypes>::applyJT(const sofa::core::ConstraintParams * /*cparams*/,
                                                                  CaribouBarycentricMapping::DataMapMapSparseMatrix & data_output_jacobian,
                                                                  const CaribouBarycentricMapping::MappedDataMapMapSparseMatrix & data_input_mapped_jacobian) {
    /* using SparseMatrix = decltype(p_J);
    using StorageIndex = typename SparseMatrix::StorageIndex;
    static constexpr auto J_is_row_major = SparseMatrix::IsRowMajor;
    // Sanity check
    if (not p_barycentric_container or not p_barycentric_container->outside_nodes().empty()) {
        return;
    }
    // With the mapping matrix J, every columns j of a given row i represent the jth shape
    // value evaluated at the ith mapped node. We want to compute H = Jt H_m where H_m is
    // the constraint matrix of the mapped DOFs. Both Jt and H_m are sparse matrices.
    // However, H and H_m are a special kind of sparse matrices having a map of map of "Deriv"
    // vector.
    auto output_jacobian = sofa::helper::WriteAccessor<DataMapMapSparseMatrix>(data_output_jacobian);
    auto input_mapped_jacobian = sofa::helper::ReadAccessor<MappedDataMapMapSparseMatrix>(data_input_mapped_jacobian);
    const auto rowEnd = input_mapped_jacobian->end();
    for (auto rowIt = input_mapped_jacobian->begin(); rowIt != rowEnd; ++rowIt) {
        auto colItEnd = rowIt.end();
        auto colIt = rowIt.begin();
        if (colIt == colItEnd) continue;
        auto output_row = output_jacobian->writeLine(rowIt.index());
        for ( ; colIt != colItEnd; ++colIt) {
            auto mapped_node_index  =  colIt.index();
            auto mapped_value = colIt.val();
            if constexpr (J_is_row_major) {
                for (typename SparseMatrix::InnerIterator it(p_J, mapped_node_index); it; ++it) {
                    const auto node_index = it.col();
                    const auto shape_value = it.value();
                    output_row.addCol(node_index, mapped_value*shape_value);
                }
            } else {
                // J is column major
                for (int node_index=0; node_index<p_J.outerSize(); ++node_index) {
                    const auto & start = p_J.outerIndexPtr()[node_index];
                    const auto & end   = p_J.outerIndexPtr()[node_index+1];
                    const auto id = p_J.data().searchLowerIndex(start, end, static_cast<StorageIndex>(mapped_node_index));
                    if ((id<end) && (p_J.data().index(id)==static_cast<StorageIndex>(mapped_node_index))) {
                        const auto shape_value = p_J.data().value(id);
                        output_row.addCol(node_index, mapped_value*shape_value);
                    }
                }
            }
        }
    } */
}

template<typename Element, typename MappedDataTypes>
void CaribouBarycentricMapping<Element, MappedDataTypes>::draw(const sofa::core::visual::VisualParams *vparams) {
    if ( !vparams->displayFlags().getShowMappings() ) return;

    if (not p_barycentric_container) return;

    using Color = sofa::type::RGBAColor;

    // Draw outside points
    if (not p_barycentric_container->outside_nodes().empty()) {
        const auto mapped_rest_positions = this->getToModel()->readRestPositions();
        const auto & outside_nodes = p_barycentric_container->outside_nodes();
        std::vector<sofa::type::Vector3> outside_nodes_positions (outside_nodes.size());
        for (std::size_t i = 0; i < outside_nodes.size(); ++i) {
            const auto & node_index = outside_nodes[i];
            for (std::size_t j = 0; j < MappedDimension; ++j) {
                outside_nodes_positions[i][j] =    mapped_rest_positions[node_index][j];
            }
        }
        vparams->drawTool()->drawPoints(outside_nodes_positions, 5, Color::red());
    }
}

template<typename Element, typename MappedDataTypes>
template<typename Derived>
auto CaribouBarycentricMapping<Element, MappedDataTypes>::canCreate(Derived * o,
                                                                    sofa::core::objectmodel::BaseContext * context,
                                                                    sofa::core::objectmodel::BaseObjectDescription * arg) -> bool {
    using namespace sofa::core::objectmodel;
    using CaribouTopology = SofaCaribou::topology::CaribouTopology<Element>;

    std::string requested_template = arg->getAttribute( "template", "");
    std::string this_template = Derived::templateName(o);

    // Multiple spaces to one space
    auto trim_spaces = [](std::string str) {
        std::string::iterator new_end =
                std::unique(str.begin(), str.end(),
                            [=](char lhs, char rhs){ return (lhs == rhs) && (lhs == ' '); }
                );
        str.erase(new_end, str.end());
        return str;
    };

    // To lower case
    auto to_lower = [](std::string str) {
        std::transform(str.begin(), str.end(), str.begin(), [](unsigned char c){ return std::tolower(c); });
        return str;
    };

    // Replace space for comma
    auto space_to_coma = [](std::string str) {
        std::replace(str.begin(), str.end(), ' ', ',');
        return str;
    };

    // Split comas to vectors
    auto split = [](std::string str) {
        std::stringstream ss(str);
        std::string item;
        std::vector<std::string> elems;
        while (std::getline(ss, item, ',')) {
             elems.push_back(std::move(item));
        }
        return elems;
    };

    const auto parsed_requested_template = split(to_lower(space_to_coma(trim_spaces(requested_template))));
    const auto parsed_this_template      = split(to_lower(space_to_coma(trim_spaces(requested_template))));
    const std::string requested_element_type = parsed_requested_template.empty() ? "" : parsed_requested_template[0];
    const std::string this_element_type      = parsed_this_template.empty() ? "" : parsed_this_template[0];

    // Simplest case, the user set the template argument and it is equal to this template specialization
    if (requested_element_type == this_element_type) {
        return Inherit1::canCreate(o, context, arg);
    }
    
    // The user set the template argument, but it doesn't match this template specialization
    if (not requested_element_type.empty()) {
        arg->logError("Requested element type is not '"+this_element_type+"'.");
        return false;
    }

    
    // The user didn't set any template argument. Let's try to deduce it.
    
    // The user specified a path to a CaribouTopology, let's check if the Element type matches
    std::string topology_path = arg->getAttribute("topology", "");

    
    if (not topology_path.empty()) {
        topology_path = topology_path.substr(1); // removes the "@"
        auto topology = context->get<CaribouTopology>(topology_path);
        if (not topology) {
            arg->logError("The element type of the given topology '" + topology_path + "' is not '"+this_element_type+"'.");
            return false;
        }
        // The topology element type matched this mapping, all good here
        return Inherit1::canCreate(o, context, arg);
    }
    
    // The user hasn't specified any path to a topology, nor he has manually set the Element type using the template argument
    // Let's try to find a matching topology in the parent or current context.
    auto * context_node = dynamic_cast<sofa::simulation::Node*>(context);
    auto * parent_context_node = (context_node->getNbParents() > 0) ? context_node->getFirstParent() : nullptr;
    CaribouTopology * topology = nullptr;

    // Search first in the parent context node (if any)
    if (parent_context_node) {
        topology = parent_context_node->getContext()->get<CaribouTopology>();
    }

    // If not found in the parent context, search in the current context
    if (not topology and (context_node != parent_context_node)) {
        topology = context_node->getContext()->get<CaribouTopology>();
    }

    if (not topology) {
        arg->logError("Cannot deduce the element type from any topology in the parent or current context nodes.");
        return false;
    }

    // We found a topology with a matching element type, let's try it. The user will be noticed of this automatic choice
    // made for him in the init method
    return Inherit1::canCreate(o, context, arg);
}

} // namespace SofaCaribou::mapping