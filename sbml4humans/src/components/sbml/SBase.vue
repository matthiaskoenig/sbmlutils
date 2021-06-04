<template>
    <div class="container">
        <p>
            <a
                class="btn btn-primary"
                data-toggle="collapse"
                href="#collapseExample"
                role="button"
                aria-expanded="false"
                aria-controls="collapseExample"
            >
                Name: {{ info.name }} SBO: {{ info.sbo }}
            </a>
        </p>
        <div class="collapse" id="collapseExample">
            <div class="card card-body">
                <ul class="sbase-info">
                    <li>SId: {{ info.id }}</li>
                    <li>Meta ID: {{ info.metaId }}</li>
                    <li>
                        CV Terms:
                        <ol class="cv-terms">
                            <li
                                v-for="cvterm in info.cvterms"
                                v-bind:key="cvterm.qualifier"
                            >
                                Qualifier: {{ cvterm.qualifier }}<br />
                                Resource: {{ cvterm.resources[0] }}
                            </li>
                        </ol>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        info: {},
    },

    data() {
        return {};
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/SBase.scss";
</style>
