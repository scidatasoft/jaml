from rdkit import Chem


def get_molecule_smiles(molecule):
    smiles = ''
    try:
        if molecule and molecule.mol:
            smiles = Chem.MolToSmiles(Chem.MolFromMolBlock(molecule.mol))
    except:
        pass

    return smiles
