from collections import OrderedDict
import xmltodict
import sklearn


class OpenMLFlow(object):
    def __init__(self, model, id=None, uploader=None,
                 description='Flow generated by openml_run', creator=None,
                 contributor=None, tag=None):
        self.id = id
        self.upoader = uploader
        self.description = description
        self.creator = creator
        self.tag = tag
        self.model = model
        self.source = "FIXME DEFINE PYTHON FLOW"
        self.name = (model.__module__ + "." +
                     model.__class__.__name__)
        self.external_version = 'Tsklearn_' + sklearn.__version__

    def generate_flow_xml(self):
        model = self.model
        flow_dict = OrderedDict()
        flow_dict['oml:flow'] = OrderedDict()
        flow_dict['oml:flow']['@xmlns:oml'] = 'http://openml.org/openml'
        flow_dict['oml:flow']['oml:name'] = self.name
        flow_dict['oml:flow']['oml:external_version'] = self.external_version
        flow_dict['oml:flow']['oml:description'] = self.description

        clf_params = model.get_params()
        flow_parameters = []
        for k, v in clf_params.items():
            # data_type, default_value, description, recommendedRange
            # type = v.__class__.__name__    Not using this because it doesn't conform standards
            # eg. int instead of integer
            param_dict = {'oml:name': k}
            flow_parameters.append(param_dict)

        flow_dict['oml:flow']['oml:parameter'] = flow_parameters

        flow_xml = xmltodict.unparse(flow_dict, pretty=True)

        # A flow may not be uploaded with the encoding specification..
        flow_xml = flow_xml.split('\n', 1)[-1]
        return flow_xml

    def publish(self, api_connector):
        """
        The 'description' is binary data of an XML file according to the XSD Schema (OUTDATED!):
        https://github.com/openml/website/blob/master/openml_OS/views/pages/rest_api/xsd/openml.implementation.upload.xsd

        (optional) file_path is the absolute path to the file that is the flow (eg. a script)
        """
        xml_description = self.generate_flow_xml()
        data = {'description': xml_description, 'source': self.source}
        return_code, return_value = api_connector._perform_api_call(
            "/flow/", data=data)
        return return_code, return_value

    def ensure_flow_exists(self, connector):
        """
        First checks if a flow exists for the given model.
        If it does, then it will return the corresponding flow id.
        If it does not, then it will create a flow, and return the flow id
        of the newly created flow.
        """
        import sklearn
        flow_version = 'Tsklearn_' + sklearn.__version__
        _, _, flow_id = check_flow_exists(connector, self.name, flow_version)

        if int(flow_id) == -1:
            return_code, response_xml = self.publish(connector)

            response_dict = xmltodict.parse(response_xml)
            flow_id = response_dict['oml:upload_flow']['oml:id']
            return int(flow_id)

        return int(flow_id)


def check_flow_exists(api_connector, name, version):
    """Retrieves the flow id of the flow uniquely identified by name+version.

    Returns flow id if such a flow exists,
    returns -1 if flow does not exists,
    http://www.openml.org/api_docs/#!/flow/get_flow_exists_name_version
    """
    if not (type(name) is str and len(name) > 0):
        raise ValueError('Parameter \'name\' should be a non-empty string')
    if not (type(version) is str and len(version) > 0):
        raise ValueError('Parameter \'version\' should be a non-empty string')

    return_code, xml_response = api_connector._perform_api_call(
        "/flow/exists/%s/%s" % (name, version))
    if return_code != 200:
        # fixme raise appropriate error
        raise ValueError("api call failed: %s" % xml_response)
    xml_dict = xmltodict.parse(xml_response)
    flow_id = xml_dict['oml:flow_exists']['oml:id']
    return return_code, xml_response, flow_id
