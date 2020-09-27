import os.path

from sbmlutils.report import sbmlreport

if __name__ == "__main__":

    # create the sbml report
    f_path = os.path.join(os.path.curdir, 'yeast_glycolysis.xml')
    print(f_path)
    sbmlreport.create_report(sbml_path=f_path, target_dir=os.path.curdir)
