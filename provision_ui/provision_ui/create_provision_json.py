import json
import sys

sys.path.append("..")

from aggregation_code.dashboard_class import StreamDash
from django.shortcuts import render
from django.template.context_processors import csrf


class PassingFieldData:
    def __init__(self, name, id, agg) -> None:
        self.name = name
        self.id = id
        self.agg = agg


def home(request):

    passing_dict = {}
    streamDashObj = StreamDash()
    streamDashObj.read_metadata(False)
    aggregateFields = set(
        [
            i
            for i in streamDashObj.all_fields_map
            if "agg" in streamDashObj.all_fields_map[i]
        ]
    )
    chosenFieldsIds = [i.id for i in streamDashObj.stream_metadata.chosen_fields]
    # 1100 -> reqtimesec
    if "1100" in chosenFieldsIds:
        passing_dict["allow_time_based_aggregation"] = 1
    else:
        passing_dict["allow_time_based_aggregation"] = 0

    fields = list(set(aggregateFields) & set(chosenFieldsIds))

    passing_fields = []

    for i in fields:
        passing_fields.append(
            PassingFieldData(
                streamDashObj.all_fields_map[i]["name"],
                i,
                streamDashObj.all_fields_map[i]["agg"],
            )
        )

    passing_dict["data"] = passing_fields
    passing_dict["custom_fields"] = streamDashObj.get_custom_fields()
    custom_fields = passing_dict["custom_fields"]

    if request.method == "POST":
        passing_dict.update(csrf(request))
        fields = {i: request.POST[i] for i in request.POST}

        del fields["csrfmiddlewaretoken"]
        normalFields = {}
        timeBwAggregationsDict = {}
        custFields = []
        for i in fields:
            if i in custom_fields:
                custFields.append(i)
            if "ChboxFunction" in i:
                try:
                    ChboxFunction, name, function = i.split("_")
                    if name in normalFields:
                        normalFields[name].append(function)
                    else:
                        normalFields[name] = [function]
                except Exception as e:
                    print(e)

            if "TimeBw2" in i:
                try:
                    time, name = i.split("_")
                    if fields[i] == "":
                        timeBwAggregationsDict[name] = -1
                    else:
                        timeBwAggregationsDict[name] = fields[i]
                except Exception as e:
                    print(e)
                    print("time\n", i, i.split("_"))

        normalFieldsWithTime = {}
        for i in normalFields:
            if i in timeBwAggregationsDict:
                normalFieldsWithTime[i] = [timeBwAggregationsDict[i], normalFields[i]]
            else:
                normalFieldsWithTime[i] = [-1, normalFields[i]]

        write_provision_to_file(streamDashObj, normalFieldsWithTime, custFields)

    return render(request, "index.html", passing_dict)


def write_provision_to_file(streamDashObj, fields, custom_fields):

    provision_file = "prov_site_with_time.json"
    d = {}
    for i in fields:
        d[i] = fields[i]
    d["custom-func"] = custom_fields

    try:
        streamDashObj.cloud_storage_object.containerClient.delete_blob(provision_file)

    except Exception as e:
        pass

    try:
        streamDashObj.cloud_storage_object.upload_file(
            provision_file, json.dumps(d, indent=4).encode("utf-8")
        )
    except Exception as e:
        print("Couldnt upload prov_site.json file", e)
