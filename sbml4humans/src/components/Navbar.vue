<template>
    <nav class="navbar navbar-dark bg-dark">
        <a class="navbar-brand" href="#">SBML4Humans</a>
        <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
        </button>

        <div class="collapse navbar-collapse" id="navbarSupportedContent">
            <ul class="navbar-nav ml-auto">
                <li class="nav-item active">
                    <router-link class="nav-link" to="/">Home</router-link>
                </li>
                <li class="nav-item">
                    <router-link class="nav-link" to="/">Upload SBML</router-link>
                </li>
            </ul>
        </div>
    </nav>
</template>

<script lang="ts">
export default{

}
</script>

<style lang="scss">
@import '../assets/styles/scss/components/Navbar.scss'
</style>
