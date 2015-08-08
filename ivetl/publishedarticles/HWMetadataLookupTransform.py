class HWMetadataLookupTransform:


    def asm_xform_doi(input_doi):

        return input_doi.replace('mbio', 'mBio').replace('/jb.', '/JB.')

    def aan_xform_doi(input_doi):

        return input_doi.replace('/wnl.', '/WNL.').replace('/cpj.', '/CPJ.').replace('/nxi.', '/NXI.')

    def asbmb_xform_doi(input_doi):

        s1 = input_doi[:12] + input_doi[12].upper() + input_doi[12+1:]

        if input_doi.startswith('10.1074/mcp'):
            s1 = s1.replace('-mcp', '-MCP')

        return s1

    def aap_xform_doi(input_doi):
        s1 = input_doi[:-2] + input_doi[-2:].upper()

        return s1

    def besbjs_xform_doi(input_doi):
        return input_doi.upper()

    def sfn_xform_doi(input_doi):
        return input_doi.upper()

    def alphamed_xform_doi(input_doi):

        if input_doi.startswith('10.1634/theoncologist'):
            input_doi = input_doi[:21] + input_doi[21:].upper()

        return input_doi

    def portland_xform_doi(input_doi):
        return input_doi.upper()

    xform_doi_dict = {
        'asm': asm_xform_doi,
        'aan': aan_xform_doi,
        'asbmb': asbmb_xform_doi,
        'aap': aap_xform_doi,
        'besbjs': besbjs_xform_doi,
        'sfn': sfn_xform_doi,
        'alphamed': alphamed_xform_doi,
        'portland': portland_xform_doi
    }

    def xform_doi(self, publisher_id, doi):

        if publisher_id in HWMetadataLookupTransform.xform_doi_dict:
            return HWMetadataLookupTransform.xform_doi_dict[publisher_id](doi)
        else:
            return doi





