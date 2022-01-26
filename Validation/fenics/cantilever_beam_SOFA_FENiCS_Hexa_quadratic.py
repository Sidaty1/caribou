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
    root.addObject('RequiredPlugin', pluginName="SofaOpenglVisual SofaBaseMechanics SofaBaseTopology SofaSparseSolver SofaImplicitOdeSolver SofaTopologyMapping SofaBoundaryCondition SofaEngine")

    p_0 = [0,0,0]
    p_1 = [1,0,0]
    p_2 = [1,1,0]
    p_3 = [0,1,0]
    p_4 = [0,0,1]
    p_5 = [1,0,1]
    p_6 = [1,1,1]
    p_7 = [0,1,1]
    p_8 = [0.5,0,0]
    p_9 = [1,0.5,0]
    p_10 = [0.5,1,0]
    p_11 = [0,0.5,0]
    p_12 = [0.5,0,1]
    p_13 = [1,0.5,1]
    p_14 = [0.5,1,1]
    p_15 = [0,0.5,1]
    p_16 = [0,0,0.5]
    p_17 = [1,0,0.5]
    p_18 = [1,1,0.5]
    p_19 = [0,1,0.5]

    position = np.array([p_0, p_1, p_2, p_3, p_4, p_5, p_6, p_7, p_8, p_9, p_10, p_11, p_12, p_13, p_14, p_15, p_16, p_17, p_18, p_19])
    # TODO improve the manual permutation for matching the redefinition of the hexahedron
    # TODO redefine the visualization of the hexaedron
    indices = np.array([4, 5, 0, 1, 7, 6, 3, 2, 12, 16, 15, 17, 13, 8, 11, 9, 14, 19, 18, 10])


    hexa_node = root.addChild("hexa_node")
    hexa_node.addObject('StaticSolver', newton_iterations="1", relative_correction_tolerance_threshold="1e-15", relative_residual_tolerance_threshold="1e-10", printLog="1")
    hexa_node.addObject('SparseLDLSolver', template="CompressedRowSparseMatrixMat3x3d")

    hexa_node.addObject('MechanicalObject', name="mo", position=position.tolist())
    hexa_node.addObject('CaribouTopology', name='topology', template='Hexahedron20', indices=indices.tolist())

    hexa_node.addObject('SaintVenantKirchhoffMaterial_FEniCS', young_modulus=3000, poisson_ratio=0.3)
    hexa_node.addObject('HyperelasticForcefield_FEniCS', printLog=True)

    hexa_node.addObject('BoxROI', name="fixed_roi", box="-7.5 -7.5 -0.9 7.5 7.5 0.1")
    hexa_node.addObject('FixedConstraint', indices="@fixed_roi.indices")
    hexa_node.addObject('BoxROI', name="top_roi", box="-7.5 -7.5 79.9 7.5 7.5 80.1")
    hexa_node.addObject('ConstantForceField', force="0 -1 0", indices="@top_roi.indices")

    test_node = root.addChild("test")
    test_node.addObject('StaticSolver', newton_iterations="1", relative_correction_tolerance_threshold="1e-15", relative_residual_tolerance_threshold="1e-10", printLog="1")
    test_node.addObject('SparseLDLSolver', template="CompressedRowSparseMatrixMat3x3d")

    test_node.addObject('MechanicalObject', name="mo", position=position.tolist())
    test_node.addObject('CaribouTopology', name='topology', template='Hexahedron20', indices=indices.tolist())

    test_node.addObject('SaintVenantKirchhoffMaterial', young_modulus=3000, poisson_ratio=0.3)
    test_node.addObject('HyperelasticForcefield', printLog=True)

    test_node.addObject('BoxROI', name="fixed_roi", box="-7.5 -7.5 -0.9 7.5 7.5 0.1")
    test_node.addObject('FixedConstraint', indices="@fixed_roi.indices")
    test_node.addObject('BoxROI', name="top_roi", box="-7.5 -7.5 79.9 7.5 7.5 80.1")
    test_node.addObject('ConstantForceField', force="0 -1 0", indices="@top_roi.indices")


    # import meshio
    # beam_q2 = meshio.read("../meshes/beam_q2.vtu")

    # # TODO improve the manual permutation for matching the redefinition of the hexahedron
    # # TODO redefine the visualization of the hexaedron
    # indices = np.empty(beam_q2.cells_dict['hexahedron20'].shape)
    # indices = beam_q2.cells_dict['hexahedron20'][:, [4, 5, 0, 1, 7, 6, 3, 2, 12, 16, 15, 17, 13, 8, 11, 9, 14, 19, 18, 10]]


    # sofa_node = root.addChild("tetra_node_SOFA")
    # sofa_node.addObject('StaticSolver', newton_iterations="25", relative_correction_tolerance_threshold="1e-15", relative_residual_tolerance_threshold="1e-10", printLog="1")
    # sofa_node.addObject('SparseLDLSolver', template="CompressedRowSparseMatrixMat3x3d")
    # sofa_node.addObject('MechanicalObject', name="mo", position=beam_q2.points.tolist())
    # sofa_node.addObject('CaribouTopology', name='topology', template='Hexahedron20', indices=indices)
    # sofa_node.addObject('BoxROI', name="fixed_roi", box="-7.5 -7.5 -0.9 7.5 7.5 0.1")
    # sofa_node.addObject('FixedConstraint', indices="@fixed_roi.indices")
    # sofa_node.addObject('BoxROI', name="top_roi", box="-7.5 -7.5 79.9 7.5 7.5 80.1")
    # sofa_node.addObject('ConstantForceField', force="0 -100 0", indices="@top_roi.indices")
    # sofa_node.addObject('SaintVenantKirchhoffMaterial', young_modulus="3000", poisson_ratio="0.3")
    # sofa_node.addObject('HyperelasticForcefield', printLog=True)


    # fenics_node = root.addChild("tetra_node_FEniCS")
    # fenics_node.addObject('StaticSolver', newton_iterations="25", relative_correction_tolerance_threshold="1e-15", relative_residual_tolerance_threshold="1e-10", printLog="1")
    # fenics_node.addObject('SparseLDLSolver', template="CompressedRowSparseMatrixMat3x3d")
    # fenics_node.addObject('MechanicalObject', name="mo", position=beam_q2.points.tolist())
    # fenics_node.addObject('CaribouTopology', name='topology', template='Hexahedron20', indices=indices)
    # fenics_node.addObject('BoxROI', name="fixed_roi", box="-7.5 -7.5 -0.9 7.5 7.5 0.1")
    # fenics_node.addObject('FixedConstraint', indices="@fixed_roi.indices")
    # fenics_node.addObject('BoxROI', name="top_roi", box="-7.5 -7.5 79.9 7.5 7.5 80.1")
    # fenics_node.addObject('ConstantForceField', force="0 -100 0", indices="@top_roi.indices")
    # fenics_node.addObject('SaintVenantKirchhoffMaterial_FEniCS', young_modulus="3000", poisson_ratio="0.3")
    # fenics_node.addObject('HyperelasticForcefield_FEniCS', printLog=True)

    return root


# Function used only if this script is called from a python environment
if __name__ == '__main__':
    main()