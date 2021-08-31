<template>
    <div class="p-d-flex p-mt-2">
        <Tag :value="qualifier" severity="success" class="qualifier"></Tag>
        <Tag :value="qualifier" severity="warning" class="resource">
            <a :href="resource" target="_blank" class="resource">{{ resource }}</a>
        </Tag>
    </div>
    <div class="p-mt-1 p-mb-3 p-ml-2" v-if="addInfo != null">
        <strong>{{ addInfo.term }}</strong
        ><span v-if="addInfo.description != null">: {{ addInfo.description }}</span>
        <br />
        <span v-if="addInfo.synonyms != null && addInfo.synonyms.length > 0"
            >Synonyms: {{ addInfo.synonyms.join() }}</span
        >
        <span v-if="addInfo.collection">Collection: {{ addInfo.collection }}</span>
        <div v-if="addInfo.xrefs && addInfo.xrefs.length > 0">
            External References:
            <div class="p-ml-3">
                <li v-for="xref in addInfo.xrefs" :key="xref">
                    <a :href="xref.url" target="_blank">{{ xref.url }}</a> ({{ xref.database }})
                </li>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import additionalInfoUtils from "@/helpers/additionalInfoUtils";

export default defineComponent({
    props: {
        qualifier: {
            type: String,
            default: "",
        },
        resource: {
            type: String,
            default: "",
        },
    },

    data() {
        return {
            addInfo: {},
        };
    },

    created() {
        const parts = this.resource.split("/");
        const resourceID = parts[parts.length - 1];
        additionalInfoUtils.fetchAdditionalInfo(resourceID).then((res) => {
            this.addInfo = res as Record<string, unknown>;
        });
    },
});
</script>

<style lang="scss" scoped>
.qualifier {
    border-radius: 5px 0 0 5px;
    padding: 0 5px !important;
}

.resource {
    color: black;
    border-radius: 0px 5px 5px 0;
}

.p-tag {
    padding: 0 5px !important;
}
</style>
