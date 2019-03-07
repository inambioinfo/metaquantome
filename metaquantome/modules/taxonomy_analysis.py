import metaquantome.modules.expand
from metaquantome.databases.NCBITaxonomyDb import NCBITaxonomyDb, BASIC_TAXONOMY_TREE
from metaquantome.util import utils


def taxonomy_analysis(df, samp_grps, data_dir, tax_colname='lca'):
    """
    Expand taxonomy annotations
    :param df: joined dataframe
    :param samp_grps: SampleGroups object
    :param data_dir: parent directory for the taxonomy database
    :param tax_colname: column with taxonomic annotations
    :return: dataframe with taxa and intensities
    """
    # if data_dir is not provided, we define the default
    if not data_dir:
        data_dir = utils.define_ontology_data_dir('taxonomy')
    # load ncbi database from data dir
    ncbi = NCBITaxonomyDb(data_dir)

    # check for numeric characters, which indicates taxid
    # if is name, convert to taxid
    # keep as character until querying ncbi database
    if utils.sniff_tax_names(df, tax_colname):
        df[tax_colname] = ncbi.convert_name_to_taxid(df[tax_colname])
    else:
        df[tax_colname] = [int(x) for x in df[tax_colname]]
    # filter df to those that tax ids that non-NaN and are present in NCBI database
    is_not_nan = df[tax_colname].notnull()
    is_in_db = df[tax_colname].apply(ncbi.is_in_db)
    df_clean = df.loc[is_not_nan & is_in_db]
    results = metaquantome.modules.expand.common_hierarchical_analysis(ncbi, df_clean, tax_colname, samp_grps)

    # use the database to get the rank for each NCBI id number
    results['rank'] = results['id'].apply(ncbi.get_rank)

    # filter out any ranks that are not in the basic taxonomy tree
    is_right_rank = results['rank'].isin(BASIC_TAXONOMY_TREE)
    results = results.loc[is_right_rank, :]

    # translate ids back to names and append name column
    results['taxon_name'] = ncbi.convert_taxid_to_name(results['id'])
    return results