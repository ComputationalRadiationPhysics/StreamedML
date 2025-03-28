import openpmd_api as io
import json
import sys

class StreamReader():
    
    def __init__(self):
        self.__init_from_config_file()
    
    def __init_from_config_file(self):
        try:
            with open(r"/home/h5/vama551b/home/streamed-ml/StreamedML/main/StreamDataReader/stream_config.json") as stream_config:
                stream = json.load(stream_config)
                self._stream_path = stream["stream_path"]
                self._meshes = stream["meshes"]
                self._particles = stream["particles"]
            self._series = self._init_stream()
            self._series_iterator = self._init_series_iterator()
        except:
            print("Unexpected error:", sys.exc_info()[0])
    
    def _init_stream(self):
        print("initialized stream")
        return io.Series(self._stream_path, io.Access_Type.read_only)
    
    def _init_series_iterator(self):
        print("initialized iterator")
        return iter(self._series.read_iterations())
    
    def _get_iteration(self):
        try:
            print("Getting NEXT")
            iteration = None
            if self._series_iterator is not None:
                iteration = next(self._series_iterator) 
            return iteration
        except StopIteration:
            return None
    
    def _get_data(self,current_iteration):
        data_dict = dict()
        data_dict["iteration_id"] = current_iteration.iteration_index
        data_dict["meshes"] = dict()
        data_dict["particles"] = dict()
        
        #mesh extraction
        for record_variable in self._meshes:
            mesh_dict = data_dict["meshes"]
            mesh_dict[record_variable] = None
            if record_variable in current_iteration.meshes:
                current_record = current_iteration.meshes[record_variable]
                if len(current_record) == 1:
                    mesh_dict[record_variable] = current_record[io.Mesh_Record_Component.SCALAR][0]
                else:
                    loadedChunks = []
                    shapes = []
                    for dim in current_record:
                        rc = current_record[dim]
                        loadedChunks.append(rc.load_chunk([0], rc.shape))
                        shapes.append(rc.shape)
                    mesh_dict[record_variable] = loadedChunks
                    if isinstance(shapes[0], int):
                         mesh_dict[str(record_variable)+"_shape"] = (len(shapes), shapes[0])
                    else:
                        shapes[0].insert(0,len(shapes))
                        mesh_dict[str(record_variable)+"_shape"] = tuple(shapes[0])
            else:
                print("Didn't find {}".format(record_variable))
                
        #particles extraction
        for record_variable in self._particles.keys():
            particles_dict = data_dict["particles"]
            if record_variable in current_iteration.particles:
                particles_dict[record_variable] = dict()
                current_particle = current_iteration.particles[record_variable]
                for component in self._particles[record_variable]:
                    particles_dict[record_variable][component] = None
                    if component in current_particle:
                        current_record = current_particle[component]
                        if len(current_record) == 1:
                            particles_dict[record_variable][component] = current_record[io.Mesh_Record_Component.SCALAR][0]
                        else:
                            loadedChunks = []
                            shapes = []
                            for dim in current_record:
                                rc = current_record[dim]
                                loadedChunks.append(rc.load_chunk([0], rc.shape))
                                shapes.append(rc.shape[0])
                            particles_dict[record_variable][component] = loadedChunks
                            if isinstance(shapes[0], int):
                                particles_dict[record_variable][str(component) + "_shape"] = (len(shapes), shapes[0])
                            else:
                                shapes[0].insert(0,len(shapes))
                                particles_dict[record_variable][str(component) + "_shape"] = tuple(shapes[0])
                    else:
                        print("Didn't find {}".format(component))
            else:
                print("Didn't find {}".format(record_variable))
        
        
        current_iteration.close()
        
        return data_dict
        
    def get_next_data(self):
        iteration = self._get_iteration()
        if iteration is not None:
            return self._get_data(iteration)
        return None