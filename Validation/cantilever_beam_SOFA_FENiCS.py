# Required import for python
import Sofa
import SofaCaribou
import numpy as np


# Choose in your script to activate or not the GUI
USE_GUI = True


def main():
    import SofaRuntime
    import Sofa.Gui
    SofaRuntime.importPlugin("SofaOpenglVisual")
    SofaRuntime.importPlugin("SofaImplicitOdeSolver")
    SofaRuntime.importPlugin("SofaLoader")

    root = Sofa.Core.Node("root")
    createScene(root)
    Sofa.Simulation.init(root)

    if not USE_GUI:
        for iteration in range(10):
            Sofa.Simulation.animate(root, root.dt.value)
    else:
        Sofa.Gui.GUIManager.Init("myscene", "qglviewer")
        Sofa.Gui.GUIManager.createGUI(root, __file__)
        Sofa.Gui.GUIManager.SetDimension(1080, 1080)
        Sofa.Gui.GUIManager.MainLoop(root)
        Sofa.Gui.GUIManager.closeGUI()


def createScene(root):
    root.addObject('DefaultVisualManagerLoop')
    root.addObject('DefaultAnimationLoop')
    root.addObject('VisualStyle', displayFlags="showForceFields showBehaviorModels")
    root.addObject('RequiredPlugin', pluginName="SofaOpenglVisual SofaSimpleForcefield SofaBaseMechanics SofaBaseTopology SofaSparseSolver SofaImplicitOdeSolver SofaTopologyMapping SofaBoundaryCondition SofaEngine")



    # p_0 = [0,0,0]
    # p_1 = [1,0,0]
    # p_2 = [1,1,0]
    # p_3 = [0,1,0]
    # p_4 = [0,0,1]
    # p_5 = [1,0,1]
    # p_6 = [1,1,1]
    # p_7 = [0,1,1]
    # position = np.array([p_0, p_1, p_2, p_3, p_4, p_5, p_6, p_7])
    # indices = np.array([0, 1, 2, 3, 4, 5, 6, 7])


    hexa_node = root.addChild("hexa_node")
    hexa_node.addObject('StaticSolver', newton_iterations="2", relative_correction_tolerance_threshold="1e-15", relative_residual_tolerance_threshold="1e-10", printLog="1")
    hexa_node.addObject('SparseLDLSolver', template="CompressedRowSparseMatrixMat3x3d")
    hexa_node.addObject('RegularGridTopology', name="grid", min="0 0 0", max="1 1 1", n="2 2 2")

    hexa_node.addObject('MechanicalObject', name="mo", src="@grid")
    hexa_node.addObject('HexahedronSetTopologyContainer', name="topology", src="@grid")
    # hexa_node.addObject('MechanicalObject', name="mo", position=position.tolist())
    # hexa_node.addObject('CaribouTopology', name='topology', template='Hexahedron', indices=indices.tolist())

    hexa_node.addObject('SaintVenantKirchhoffMaterial_FEniCS', young_modulus=3000, poisson_ratio=0.3)
    hexa_node.addObject('HyperelasticForcefield_FEniCS', printLog=True)

    hexa_node.addObject('BoxROI', name="fixed_roi", box="-7.5 -7.5 -0.9 7.5 7.5 0.1")
    hexa_node.addObject('FixedConstraint', indices="@fixed_roi.indices")
    hexa_node.addObject('BoxROI', name="top_roi", box="-7.5 -7.5 79.9 7.5 7.5 80.1")
    hexa_node.addObject('ConstantForceField', force="0 -10 0", indices="@top_roi.indices")


    test_node = root.addChild("test")
    test_node.addObject('RegularGridTopology', name="grid", min="0 0 0", max="1 1 1", n="2 2 2")
    test_node.addObject('StaticSolver', newton_iterations="2", relative_correction_tolerance_threshold="1e-15", relative_residual_tolerance_threshold="1e-10", printLog="1")
    test_node.addObject('SparseLDLSolver', template="CompressedRowSparseMatrixMat3x3d")

    test_node.addObject('MechanicalObject', name="mo", src="@grid")
    test_node.addObject('HexahedronSetTopologyContainer', name="topology", src="@grid")
    # test_node.addObject('MechanicalObject', name="mo", position=position.tolist())
    # test_node.addObject('CaribouTopology', name='topology', template='Hexahedron', indices=indices.tolist())

    test_node.addObject('SaintVenantKirchhoffMaterial', young_modulus=3000, poisson_ratio=0.3)
    test_node.addObject('HyperelasticForcefield', printLog=True)

    test_node.addObject('BoxROI', name="fixed_roi", box="-7.5 -7.5 -0.9 7.5 7.5 0.1")
    test_node.addObject('FixedConstraint', indices="@fixed_roi.indices")
    test_node.addObject('BoxROI', name="top_roi", box="-7.5 -7.5 79.9 7.5 7.5 80.1")
    test_node.addObject('ConstantForceField', force="0 -10 0", indices="@top_roi.indices")

    # hexa_node = root.addChild("hexa_node")
    # hexa_node.addObject('StaticSolver', newton_iterations="25", relative_correction_tolerance_threshold="1e-15", relative_residual_tolerance_threshold="1e-10", printLog="1")
    # hexa_node.addObject('SparseLDLSolver', template="CompressedRowSparseMatrixMat3x3d")
    # hexa_node.addObject('RegularGridTopology', name="grid", min="-7.5 -7.5 0", max="7.5 7.5 80", n="9 9 21")

    # hexa_node.addObject('MechanicalObject', name="mo", src="@grid")
    # hexa_node.addObject('TetrahedronSetTopologyContainer', name="topology")
    # hexa_node.addObject('TetrahedronSetTopologyModifier')
    # hexa_node.addObject('Hexa2TetraTopologicalMapping', input="@grid", output="@topology", swapping="1")

    # hexa_node.addObject('SaintVenantKirchhoffMaterial_FEniCS', young_modulus=3000, poisson_ratio=0.3)
    # hexa_node.addObject('HyperelasticForcefield_FEniCS', printLog=True)

    # hexa_node.addObject('BoxROI', name="fixed_roi", box="-7.5 -7.5 -0.9 7.5 7.5 0.1")
    # hexa_node.addObject('FixedConstraint', indices="@fixed_roi.indices")
    # hexa_node.addObject('BoxROI', name="top_roi", box="-7.5 -7.5 79.9 7.5 7.5 80.1")
    # hexa_node.addObject('ConstantForceField', force="0 -10 0", indices="@top_roi.indices")


    # test_node = root.addChild("test")
    # test_node.addObject('RegularGridTopology', name="grid", min="-7.5 -7.5 0", max="7.5 7.5 80", n="9 9 21")
    # test_node.addObject('StaticSolver', newton_iterations="25", relative_correction_tolerance_threshold="1e-15", relative_residual_tolerance_threshold="1e-10", printLog="1")
    # test_node.addObject('SparseLDLSolver', template="CompressedRowSparseMatrixMat3x3d")

    # test_node.addObject('MechanicalObject', name="mo", src="@grid")
    # test_node.addObject('TetrahedronSetTopologyContainer', name="topology")
    # test_node.addObject('TetrahedronSetTopologyModifier')
    # test_node.addObject('Hexa2TetraTopologicalMapping', input="@grid", output="@topology", swapping="1")

    # test_node.addObject('SaintVenantKirchhoffMaterial', young_modulus=3000, poisson_ratio=0.3)
    # test_node.addObject('HyperelasticForcefield', printLog=True)

    # test_node.addObject('BoxROI', name="fixed_roi", box="-7.5 -7.5 -0.9 7.5 7.5 0.1")
    # test_node.addObject('FixedConstraint', indices="@fixed_roi.indices")
    # test_node.addObject('BoxROI', name="top_roi", box="-7.5 -7.5 79.9 7.5 7.5 80.1")
    # test_node.addObject('ConstantForceField', force="0 -10 0", indices="@top_roi.indices")


    # test_node = root.addChild("test")
    # test_node.addObject('RegularGridTopology', name="grid", min="-7.5 -7.5 0", max="7.5 7.5 80", n="9 9 21")
    # test_node.addObject('StaticSolver', newton_iterations="25", relative_correction_tolerance_threshold="1e-15", relative_residual_tolerance_threshold="1e-10", printLog="1")
    # test_node.addObject('SparseLDLSolver', template="CompressedRowSparseMatrixMat3x3d")

    # test_node.addObject('MechanicalObject', name="mo", src="@grid")
    # test_node.addObject('TetrahedronSetTopologyContainer', name="topology")
    # test_node.addObject('TetrahedronSetTopologyModifier')
    # test_node.addObject('Hexa2TetraTopologicalMapping', input="@grid", output="@topology", swapping="1")

    # test_node.addObject('SVKElasticForcefield_FEniCS', youngModulus="3000", poissonRatio="0.3", topology="@topology")

    # test_node.addObject('BoxROI', name="fixed_roi", box="-7.5 -7.5 -0.9 7.5 7.5 0.1")
    # test_node.addObject('FixedConstraint', indices="@fixed_roi.indices")
    # test_node.addObject('BoxROI', name="top_roi", box="-7.5 -7.5 79.9 7.5 7.5 80.1")
    # test_node.addObject('ConstantForceField', force="0 -10 0", indices="@top_roi.indices")

    # import meshio
    # beam_p1 = meshio.read("./meshes/beam_p1.vtu")

    # sofa_node = root.addChild("tetra_node_SOFA")
    # sofa_node.addObject('StaticSolver', newton_iterations="25", relative_correction_tolerance_threshold="1e-15", relative_residual_tolerance_threshold="1e-10", printLog="1")
    # sofa_node.addObject('SparseLDLSolver', template="CompressedRowSparseMatrixMat3x3d")
    # sofa_node.addObject('MechanicalObject', name="mo", position=beam_p1.points.tolist())
    # sofa_node.addObject('CaribouTopology', name='topology', template='Tetrahedron', indices=beam_p1.cells_dict['tetra'].tolist())
    # sofa_node.addObject('BoxROI', name="fixed_roi", box="-7.5 -7.5 -0.9 7.5 7.5 0.1")
    # sofa_node.addObject('FixedConstraint', indices="@fixed_roi.indices")
    # sofa_node.addObject('BoxROI', name="top_roi", box="-7.5 -7.5 79.9 7.5 7.5 80.1")
    # sofa_node.addObject('ConstantForceField', force="0 -10 0", indices="@top_roi.indices")
    # sofa_node.addObject('SaintVenantKirchhoffMaterial', young_modulus="3000", poisson_ratio="0.3")
    # sofa_node.addObject('HyperelasticForcefield', printLog=True)


    # fenics_node = root.addChild("tetra_node_FEniCS")
    # fenics_node.addObject('StaticSolver', newton_iterations="25", relative_correction_tolerance_threshold="1e-15", relative_residual_tolerance_threshold="1e-10", printLog="1")
    # fenics_node.addObject('SparseLDLSolver', template="CompressedRowSparseMatrixMat3x3d")
    # fenics_node.addObject('MechanicalObject', name="mo", position=beam_p1.points.tolist())
    # fenics_node.addObject('CaribouTopology', name='topology', template='Tetrahedron', indices=beam_p1.cells_dict['tetra'].tolist())
    # fenics_node.addObject('BoxROI', name="fixed_roi", box="-7.5 -7.5 -0.9 7.5 7.5 0.1")
    # fenics_node.addObject('FixedConstraint', indices="@fixed_roi.indices")
    # fenics_node.addObject('BoxROI', name="top_roi", box="-7.5 -7.5 79.9 7.5 7.5 80.1")
    # fenics_node.addObject('ConstantForceField', force="0 -10 0", indices="@top_roi.indices")
    # fenics_node.addObject('SaintVenantKirchhoffMaterial_FEniCS', young_modulus="3000", poisson_ratio="0.3")
    # fenics_node.addObject('HyperelasticForcefield_FEniCS', printLog=True)

    # import meshio
    # beam_p1 = meshio.read("./meshes/beam_p2.vtu")

    # sofa_node = root.addChild("tetra_node_SOFA")
    # sofa_node.addObject('StaticSolver', newton_iterations="2", relative_correction_tolerance_threshold="1e-15", relative_residual_tolerance_threshold="1e-10", printLog="1")
    # sofa_node.addObject('SparseLDLSolver', template="CompressedRowSparseMatrixMat3x3d")
    # sofa_node.addObject('MechanicalObject', name="mo", position=beam_p1.points.tolist())
    # sofa_node.addObject('CaribouTopology', name='topology', template='Tetrahedron10', indices=beam_p1.cells_dict['tetra10'].tolist())
    # sofa_node.addObject('BoxROI', name="fixed_roi", box="-7.5 -7.5 -0.9 7.5 7.5 0.1")
    # sofa_node.addObject('FixedConstraint', indices="@fixed_roi.indices")
    # sofa_node.addObject('BoxROI', name="top_roi", box="-7.5 -7.5 79.9 7.5 7.5 80.1")
    # sofa_node.addObject('ConstantForceField', force="0 -10 0", indices="@top_roi.indices")
    # sofa_node.addObject('SaintVenantKirchhoffMaterial', young_modulus="3000", poisson_ratio="0.3")
    # sofa_node.addObject('HyperelasticForcefield', printLog=True)


    # fenics_node = root.addChild("tetra_node_FEniCS")
    # fenics_node.addObject('StaticSolver', newton_iterations="2", relative_correction_tolerance_threshold="1e-15", relative_residual_tolerance_threshold="1e-10", printLog="1")
    # fenics_node.addObject('SparseLDLSolver', template="CompressedRowSparseMatrixMat3x3d")
    # fenics_node.addObject('MechanicalObject', name="mo", position=beam_p1.points.tolist())
    # fenics_node.addObject('CaribouTopology', name='topology', template='Tetrahedron10', indices=beam_p1.cells_dict['tetra10'].tolist())
    # fenics_node.addObject('BoxROI', name="fixed_roi", box="-7.5 -7.5 -0.9 7.5 7.5 0.1")
    # fenics_node.addObject('FixedConstraint', indices="@fixed_roi.indices")
    # fenics_node.addObject('BoxROI', name="top_roi", box="-7.5 -7.5 79.9 7.5 7.5 80.1")
    # fenics_node.addObject('ConstantForceField', force="0 -10 0", indices="@top_roi.indices")
    # fenics_node.addObject('SaintVenantKirchhoffMaterial_FEniCS', young_modulus="3000", poisson_ratio="0.3")
    # fenics_node.addObject('HyperelasticForcefield_FEniCS', printLog=True)


    # import meshio
    # beam_p1 = meshio.read("./meshes/beam_q1.vtu")

    # sofa_node = root.addChild("tetra_node_SOFA")
    # sofa_node.addObject('StaticSolver', newton_iterations="2", relative_correction_tolerance_threshold="1e-15", relative_residual_tolerance_threshold="1e-10", printLog="1")
    # sofa_node.addObject('SparseLDLSolver', template="CompressedRowSparseMatrixMat3x3d")
    # sofa_node.addObject('MechanicalObject', name="mo", position=beam_p1.points.tolist())
    # sofa_node.addObject('CaribouTopology', name='topology', template='Hexahedron', indices=beam_p1.cells_dict['hexahedron'].tolist())
    # sofa_node.addObject('BoxROI', name="fixed_roi", box="-7.5 -7.5 -0.9 7.5 7.5 0.1")
    # sofa_node.addObject('FixedConstraint', indices="@fixed_roi.indices")
    # sofa_node.addObject('BoxROI', name="top_roi", box="-7.5 -7.5 79.9 7.5 7.5 80.1")
    # sofa_node.addObject('ConstantForceField', force="0 -10 0", indices="@top_roi.indices")
    # sofa_node.addObject('SaintVenantKirchhoffMaterial', young_modulus="3000", poisson_ratio="0.3")
    # sofa_node.addObject('HyperelasticForcefield', printLog=True)


    # fenics_node = root.addChild("tetra_node_FEniCS")
    # fenics_node.addObject('StaticSolver', newton_iterations="2", relative_correction_tolerance_threshold="1e-15", relative_residual_tolerance_threshold="1e-10", printLog="1")
    # fenics_node.addObject('SparseLDLSolver', template="CompressedRowSparseMatrixMat3x3d")
    # fenics_node.addObject('MechanicalObject', name="mo", position=beam_p1.points.tolist())
    # fenics_node.addObject('CaribouTopology', name='topology', template='Hexahedron', indices=beam_p1.cells_dict['hexahedron'].tolist())
    # fenics_node.addObject('BoxROI', name="fixed_roi", box="-7.5 -7.5 -0.9 7.5 7.5 0.1")
    # fenics_node.addObject('FixedConstraint', indices="@fixed_roi.indices")
    # fenics_node.addObject('BoxROI', name="top_roi", box="-7.5 -7.5 79.9 7.5 7.5 80.1")
    # fenics_node.addObject('ConstantForceField', force="0 -10 0", indices="@top_roi.indices")
    # fenics_node.addObject('SaintVenantKirchhoffMaterial_FEniCS', young_modulus="3000", poisson_ratio="0.3")
    # fenics_node.addObject('HyperelasticForcefield_FEniCS', printLog=True)

    return root


# Function used only if this script is called from a python environment
if __name__ == '__main__':
    main()